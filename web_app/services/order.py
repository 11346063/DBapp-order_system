from datetime import date

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from web_app.services.store_settings import get_settings
from web_app.enums import SpicyLevel
from web_app.models import Identity, Menu, Order, OrderItem, OrderItemOption, Options
from web_app.services import cart as cart_service
from web_app.services.exceptions import (
    CheckoutPhoneRequired,
    EmptyCartError,
    NotFoundError,
    StaffCustomerPhoneRequired,
    ValidationServiceError,
)
from web_app.utils.phone import PhoneValidationError, normalize_tw_mobile


def is_staff_order_user(user):
    return user.is_authenticated and user.identity in (
        Identity.ADMIN,
        Identity.EMPLOYEE,
    )


def _non_negative_int(value, default=0):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def normalize_customer_phone(phone_number):
    try:
        return normalize_tw_mobile(phone_number)
    except PhoneValidationError as exc:
        raise ValidationServiceError(
            "請輸入有效的手機號碼，例如 0912345678 或 +886912345678"
        ) from exc


def normalize_checkout_data(data):
    spicy_level = SpicyLevel.from_label(data.get("spicy_level", SpicyLevel.NONE.label))
    return {
        "remark": data.get("remark", "").strip()[:200],
        "customer_phone": normalize_customer_phone(data.get("customer_phone", "")),
        "spicy_level": int(spicy_level),
        "extra_garlic_qty": _non_negative_int(data.get("extra_garlic_qty", 0)),
        "extra_basil_qty": _non_negative_int(data.get("extra_basil_qty", 0)),
    }


def generate_pickup_code(customer_phone: str) -> str:
    """
    以電話號碼尾碼產生當日唯一取餐號碼。
    先取後 3 碼；若今日已有相同號碼，往前再拿一碼（後 4 碼），依此類推。
    電話用盡時以完整數字部分作為 fallback。
    """
    digits = "".join(c for c in customer_phone if c.isdigit())
    today = date.today()
    for length in range(3, len(digits) + 1):
        code = digits[-length:]
        if not Order.objects.filter(created_at__date=today, pickup_code=code).exists():
            return code
    return digits  # fallback：完整電話數字，極不可能到達


def order_status_counts():
    status = Order.OrderStatus
    result = Order.objects.aggregate(
        submitted=Count("pk", filter=Q(status=status.SUBMITTED)),
        accepted=Count("pk", filter=Q(status=status.ACCEPTED)),
        ready=Count("pk", filter=Q(status=status.READY)),
        completed=Count("pk", filter=Q(status=status.COMPLETED)),
        cancelled=Count("pk", filter=Q(status=status.CANCELLED)),
    )
    return {
        status.SUBMITTED: result["submitted"],
        status.ACCEPTED: result["accepted"],
        status.READY: result["ready"],
        status.COMPLETED: result["completed"],
        status.CANCELLED: result["cancelled"],
    }


async def async_order_status_counts():
    status = Order.OrderStatus
    result = await Order.objects.aaggregate(
        submitted=Count("pk", filter=Q(status=status.SUBMITTED)),
        accepted=Count("pk", filter=Q(status=status.ACCEPTED)),
        ready=Count("pk", filter=Q(status=status.READY)),
        completed=Count("pk", filter=Q(status=status.COMPLETED)),
        cancelled=Count("pk", filter=Q(status=status.CANCELLED)),
    )
    return {
        status.SUBMITTED: result["submitted"],
        status.ACCEPTED: result["accepted"],
        status.READY: result["ready"],
        status.COMPLETED: result["completed"],
        status.CANCELLED: result["cancelled"],
    }


def format_order_options(raw_opts):
    s = get_settings()
    parts = []
    for option_link in raw_opts:
        name = option_link.opt.name
        level = option_link.level
        if name == s.option_name_spicy:
            parts.append(SpicyLevel.display(level))
        elif name == s.option_name_garlic:
            parts.append(f"加蒜頭x{level}")
        elif name == s.option_name_basil:
            parts.append(f"加九層塔x{level}")
        elif option_link.opt.is_custom_extra:
            parts.append(name)
    return "｜".join(parts)


def format_order_option_tags(raw_opts):
    s = get_settings()
    tags = []
    for option_link in raw_opts:
        name = option_link.opt.name
        level = option_link.level
        if name == s.option_name_spicy:
            label = SpicyLevel.display(level)
            if level == SpicyLevel.NONE:
                css = "text-white"
                style = "background-color:#9a7200;"
            else:
                css = "bg-danger text-white"
                style = ""
        elif name == s.option_name_garlic:
            label = f"加蒜頭x{level}"
            css = "bg-primary text-white"
            style = ""
        elif name == s.option_name_basil:
            label = f"加九層塔x{level}"
            css = "bg-primary text-white"
            style = ""
        elif option_link.opt.is_custom_extra:
            label = name
            css = "bg-success text-white"
            style = ""
        else:
            continue
        tags.append({"label": label, "css": css, "style": style})
    return tags


_ALLOWED_STATUS_UPDATE = frozenset(
    [Order.OrderStatus.COMPLETED, Order.OrderStatus.CANCELLED]
)


def update_order_status(order_id, status):
    if status not in _ALLOWED_STATUS_UPDATE:
        raise ValidationServiceError("不允許此狀態轉換")
    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist as exc:
            raise NotFoundError("找不到此訂單") from exc

        order.status = status
        order.save(update_fields=["status"])
    return {"status_counts": order_status_counts()}


def mark_order_ready(order_id):
    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist as exc:
            raise NotFoundError("找不到此訂單") from exc

        if order.status != Order.OrderStatus.ACCEPTED:
            raise ValidationServiceError("只有備餐中的訂單才能通知取餐")

        now = timezone.now()
        order.status = Order.OrderStatus.READY
        order.ready_at = now
        order.ready_notified_at = now
        order.save(update_fields=["status", "ready_at", "ready_notified_at"])
    return {"status_counts": order_status_counts()}


def accept_order(order_id, staff_user, estimated_wait_minutes):
    if not (1 <= estimated_wait_minutes <= 180):
        raise ValidationServiceError("等待時間必須在 1 到 180 分鐘之間")

    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist as exc:
            raise NotFoundError("找不到此訂單") from exc

        if order.status != Order.OrderStatus.SUBMITTED:
            raise ValidationServiceError("只有等待接單的訂單才能接單")

        now = timezone.now()
        order.status = Order.OrderStatus.ACCEPTED
        order.accepted_at = now
        order.accepted_by = staff_user
        order.estimated_wait_minutes = estimated_wait_minutes
        order.pickup_code = generate_pickup_code(order.customer_phone)
        order.save(
            update_fields=[
                "status",
                "accepted_at",
                "accepted_by",
                "estimated_wait_minutes",
                "pickup_code",
            ]
        )
    return {
        "order_id": order.pk,
        "status": order.status,
        "estimated_wait_minutes": estimated_wait_minutes,
        "accepted_at": order.accepted_at.isoformat(),
        "pickup_code": order.pickup_code,
        "status_counts": order_status_counts(),
    }


def create_order_from_cart(user, session, checkout_data):
    cart_service.ensure_prices_current(user, session)
    cart = cart_service.get_cart(user, session)
    if not cart:
        raise EmptyCartError("購物車是空的")

    data = normalize_checkout_data(checkout_data)
    is_staff_order = is_staff_order_user(user)
    if not data["customer_phone"] and user.is_authenticated and not is_staff_order:
        data["customer_phone"] = normalize_customer_phone(user.phone_number)
    if is_staff_order and not data["customer_phone"]:
        raise StaffCustomerPhoneRequired("員工代客點餐需要填寫電話")
    if not data["customer_phone"]:
        raise CheckoutPhoneRequired("結帳需要填寫聯絡電話")

    s = get_settings()

    # 解析勾選的自定義加料選項 IDs
    selected_custom_ids = [
        int(key[len("custom_option_") :])
        for key in checkout_data
        if key.startswith("custom_option_") and checkout_data[key]
    ]
    custom_opts = (
        list(
            Options.objects.filter(
                pk__in=selected_custom_ids, is_custom_extra=True, is_active=True
            )
        )
        if selected_custom_ids
        else []
    )
    custom_cost = sum(opt.price for opt in custom_opts)

    total = cart_service.cart_total(cart)
    extra_cost = (
        data["extra_garlic_qty"] + data["extra_basil_qty"]
    ) * s.extra_ingredient_cost
    price_total = total + extra_cost + custom_cost

    initial_status = (
        Order.OrderStatus.ACCEPTED if is_staff_order else Order.OrderStatus.SUBMITTED
    )
    system_option_names = [
        s.option_name_spicy,
        s.option_name_garlic,
        s.option_name_basil,
        s.option_name_cut,
    ]
    with transaction.atomic():
        order = Order.objects.create(
            user=user if user.is_authenticated else None,
            status=initial_status,
            price_total=price_total,
            remark=data["remark"],
            customer_phone=data["customer_phone"],
        )

        opts = {
            option.name: option
            for option in Options.objects.filter(name__in=system_option_names)
        }

        for item in cart:
            try:
                menu = Menu.objects.get(pk=item["menu_id"])
            except Menu.DoesNotExist as exc:
                raise NotFoundError(
                    "購物車中有餐點已下架或不存在，請重新整理購物車"
                ) from exc

            order_item = OrderItem.objects.create(
                order=order,
                menu=menu,
                amount=item["quantity"],
                total_price=item["subtotal"],
            )

            for opt_data in item.get("options", []):
                opt_id = opt_data.get("id")
                if opt_id and opt_id != 0:
                    OrderItemOption.objects.create(
                        order_item=order_item,
                        opt_id=opt_id,
                        level=int(opt_data.get("level", 1)),
                    )

        if s.option_name_spicy in opts:
            OrderItemOption.objects.create(
                order=order, opt=opts[s.option_name_spicy], level=data["spicy_level"]
            )
        if data["extra_garlic_qty"] > 0 and s.option_name_garlic in opts:
            OrderItemOption.objects.create(
                order=order,
                opt=opts[s.option_name_garlic],
                level=data["extra_garlic_qty"],
            )
        if data["extra_basil_qty"] > 0 and s.option_name_basil in opts:
            OrderItemOption.objects.create(
                order=order,
                opt=opts[s.option_name_basil],
                level=data["extra_basil_qty"],
            )

        for custom_opt in custom_opts:
            OrderItemOption.objects.create(order=order, opt=custom_opt, level=1)

        cart_service.clear_cart(user, session)

    return order


def create_staff_order_from_items(user, validated_data):
    """不經過購物車直接建立代客訂單（status=ACCEPTED，自動接單）。"""
    raw_phone = (validated_data.get("customer_phone") or "").strip()
    if not raw_phone:
        raise StaffCustomerPhoneRequired("員工代客點餐需要填寫電話")

    data = normalize_checkout_data(
        {
            "customer_phone": raw_phone,
            "spicy_level": validated_data.get("spicy_level", "不辣"),
            "extra_garlic_qty": validated_data.get("extra_garlic_qty", 0),
            "extra_basil_qty": validated_data.get("extra_basil_qty", 0),
            "remark": validated_data.get("remark", ""),
        }
    )

    items = validated_data.get("items") or []
    if not items:
        raise EmptyCartError("訂單沒有品項")

    s = get_settings()
    selected_custom_ids = validated_data.get("custom_options") or []
    custom_opts = (
        list(
            Options.objects.filter(
                pk__in=selected_custom_ids, is_custom_extra=True, is_active=True
            )
        )
        if selected_custom_ids
        else []
    )
    custom_cost = sum(opt.price for opt in custom_opts)

    menu_ids = [item["menu_id"] for item in items]
    menus_by_id = {m.pk: m for m in Menu.objects.filter(pk__in=menu_ids, status=True)}

    missing = [mid for mid in menu_ids if mid not in menus_by_id]
    if missing:
        raise ValidationServiceError(f"以下品項不存在或已下架：{missing}")

    menu_total = sum(menus_by_id[item["menu_id"]].price * item["qty"] for item in items)
    extra_cost = (
        data["extra_garlic_qty"] + data["extra_basil_qty"]
    ) * s.extra_ingredient_cost
    price_total = menu_total + extra_cost + custom_cost

    pickup_code = generate_pickup_code(data["customer_phone"])
    system_option_names = [
        s.option_name_spicy,
        s.option_name_garlic,
        s.option_name_basil,
    ]

    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            status=Order.OrderStatus.ACCEPTED,
            price_total=price_total,
            remark=data["remark"],
            customer_phone=data["customer_phone"],
            accepted_at=timezone.now(),
            accepted_by=user,
            pickup_code=pickup_code,
        )

        opts = {
            option.name: option
            for option in Options.objects.filter(name__in=system_option_names)
        }

        for item_data in items:
            menu = menus_by_id[item_data["menu_id"]]
            order_item = OrderItem.objects.create(
                order=order,
                menu=menu,
                amount=item_data["qty"],
                total_price=menu.price * item_data["qty"],
            )
            for opt_data in item_data.get("options") or []:
                opt_id = opt_data.get("id")
                if opt_id and opt_id != 0:
                    OrderItemOption.objects.create(
                        order_item=order_item,
                        opt_id=opt_id,
                        level=int(opt_data.get("level", 1)),
                    )

        if s.option_name_spicy in opts:
            OrderItemOption.objects.create(
                order=order, opt=opts[s.option_name_spicy], level=data["spicy_level"]
            )
        if data["extra_garlic_qty"] > 0 and s.option_name_garlic in opts:
            OrderItemOption.objects.create(
                order=order,
                opt=opts[s.option_name_garlic],
                level=data["extra_garlic_qty"],
            )
        if data["extra_basil_qty"] > 0 and s.option_name_basil in opts:
            OrderItemOption.objects.create(
                order=order,
                opt=opts[s.option_name_basil],
                level=data["extra_basil_qty"],
            )
        for custom_opt in custom_opts:
            OrderItemOption.objects.create(order=order, opt=custom_opt, level=1)

    return order


def reorder_to_cart(user, session, order_id):
    try:
        order = Order.objects.get(pk=order_id, user=user)
    except Order.DoesNotExist as exc:
        raise NotFoundError("找不到此訂單") from exc

    items = OrderItem.objects.filter(order=order).select_related("menu")
    added = 0

    for item in items:
        try:
            added += cart_service.append_menu_item_to_cart(
                user,
                session,
                item.menu,
                item.amount,
            )
        except Menu.DoesNotExist:
            continue

    return {
        "added": added,
        "cart_count": cart_service.cart_count(cart_service.get_cart(user, session)),
    }
