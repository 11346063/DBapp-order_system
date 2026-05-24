from datetime import date

from django.db import models, transaction
from django.utils import timezone

from web_app.constants import (
    EXTRA_INGREDIENT_COST,
    OPTION_BASIL,
    OPTION_GARLIC,
    OPTION_SPICY,
    SYSTEM_OPTION_NAMES,
)
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


class SpicyLevel(models.IntegerChoices):
    NONE = 0, "不辣"
    MILD = 1, "小辣"
    MEDIUM = 2, "中辣"
    HOT = 3, "大辣"

    @classmethod
    def from_label(cls, label):
        label = (label or "").strip()
        for level in cls:
            if level.label == label:
                return level
        return cls.NONE

    @classmethod
    def display(cls, value):
        try:
            return cls(value).label
        except ValueError:
            return f"辣度{value}"


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
    return {
        status.SUBMITTED: Order.objects.filter(status=status.SUBMITTED).count(),
        status.ACCEPTED: Order.objects.filter(status=status.ACCEPTED).count(),
        status.READY: Order.objects.filter(status=status.READY).count(),
        status.COMPLETED: Order.objects.filter(status=status.COMPLETED).count(),
        status.CANCELLED: Order.objects.filter(status=status.CANCELLED).count(),
    }


def format_order_options(raw_opts):
    parts = []
    for option_link in raw_opts:
        name = option_link.opt.name
        level = option_link.level
        if name == OPTION_SPICY:
            parts.append(SpicyLevel.display(level))
        elif name == OPTION_GARLIC:
            parts.append(f"加蒜頭x{level}")
        elif name == OPTION_BASIL:
            parts.append(f"加九層塔x{level}")
    return "｜".join(parts)


def update_order_status(order_id, status):
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise NotFoundError("找不到此訂單") from exc

    order.status = status
    order.save(update_fields=["status"])
    return {"status_counts": order_status_counts()}


def mark_order_ready(order_id):
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise NotFoundError("找不到此訂單") from exc

    if order.status != Order.OrderStatus.ACCEPTED:
        from web_app.services.exceptions import ValidationServiceError

        raise ValidationServiceError("只有備餐中的訂單才能通知取餐")

    now = timezone.now()
    order.status = Order.OrderStatus.READY
    order.ready_at = now
    order.ready_notified_at = now
    order.save(update_fields=["status", "ready_at", "ready_notified_at"])
    return {"status_counts": order_status_counts()}


def accept_order(order_id, staff_user, estimated_wait_minutes):
    from web_app.services.exceptions import ValidationServiceError

    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise NotFoundError("找不到此訂單") from exc

    if order.status != Order.OrderStatus.SUBMITTED:
        raise ValidationServiceError("只有等待接單的訂單才能接單")

    if not (1 <= estimated_wait_minutes <= 180):
        raise ValidationServiceError("等待時間必須在 1 到 180 分鐘之間")

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

    total = cart_service.cart_total(cart)
    extra_cost = (
        data["extra_garlic_qty"] + data["extra_basil_qty"]
    ) * EXTRA_INGREDIENT_COST
    price_total = total + extra_cost

    initial_status = (
        Order.OrderStatus.ACCEPTED if is_staff_order else Order.OrderStatus.SUBMITTED
    )
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
            for option in Options.objects.filter(name__in=SYSTEM_OPTION_NAMES)
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

        if OPTION_SPICY in opts:
            OrderItemOption.objects.create(
                order=order, opt=opts[OPTION_SPICY], level=data["spicy_level"]
            )
        if data["extra_garlic_qty"] > 0 and OPTION_GARLIC in opts:
            OrderItemOption.objects.create(
                order=order, opt=opts[OPTION_GARLIC], level=data["extra_garlic_qty"]
            )
        if data["extra_basil_qty"] > 0 and OPTION_BASIL in opts:
            OrderItemOption.objects.create(
                order=order, opt=opts[OPTION_BASIL], level=data["extra_basil_qty"]
            )

        cart_service.clear_cart(user, session)

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
