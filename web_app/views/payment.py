from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext as _
from web_app.models import Identity, Order, OrderItem, OrderItemOptions, Options, Menu

SPICY_LEVEL_MAP = {"不辣": 0, "小辣": 1, "中辣": 2, "大辣": 3}


def _is_staff_order_user(user):
    return user.is_authenticated and user.identity in (
        Identity.ADMIN,
        Identity.EMPLOYEE,
    )


def payment_view(request):
    cart = request.session.get("cart", [])
    if not cart:
        messages.warning(request, _("購物車是空的"))
        return redirect("web_app:home")

    total = sum(item["subtotal"] for item in cart)
    return render(
        request,
        "payment.html",
        {
            "cart_items": cart,
            "total": total,
            "is_guest": not request.user.is_authenticated,
            "is_staff_order": _is_staff_order_user(request.user),
        },
    )


def order_submit(request):
    if request.method != "POST":
        return redirect("web_app:payment")

    cart = request.session.get("cart", [])
    if not cart:
        messages.warning(request, _("購物車是空的"))
        return redirect("web_app:home")

    total = sum(item["subtotal"] for item in cart)

    remark = request.POST.get("remark", "").strip()[:200]
    is_staff_order = _is_staff_order_user(request.user)
    customer_phone = request.POST.get("customer_phone", "").strip()[:20]
    if is_staff_order and not customer_phone:
        messages.error(request, _("員工代客點餐需要填寫電話"))
        return redirect("web_app:payment")

    spicy_text = request.POST.get("spicy_level", "不辣").strip()
    spicy_level = SPICY_LEVEL_MAP.get(spicy_text, 0)

    try:
        extra_garlic_qty = max(0, int(request.POST.get("extra_garlic_qty", 0)))
    except ValueError:
        extra_garlic_qty = 0
    try:
        extra_basil_qty = max(0, int(request.POST.get("extra_basil_qty", 0)))
    except ValueError:
        extra_basil_qty = 0

    extra_cost = (extra_garlic_qty + extra_basil_qty) * 10
    price_total = total + extra_cost

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        create_time=timezone.now(),
        status=0,
        price_total=price_total,
        remark=remark,
        customer_phone=customer_phone if is_staff_order else "",
    )

    # 預載 Options 對照表（一次查詢）
    opts = {
        o.name: o
        for o in Options.objects.filter(name__in=["辣度", "加蒜", "九層塔", "切"])
    }

    for item in cart:
        try:
            menu = Menu.objects.get(pk=item["menu_id"])
        except Menu.DoesNotExist:
            continue

        order_item = OrderItem.objects.create(
            order=order,
            menu=menu,
            amount=item["quantity"],
            total_price=item["subtotal"],
        )

        # 寫入 item-level 選項（切法）
        for opt_data in item.get("options", []):
            opt_id = opt_data.get("id")
            if opt_id and opt_id != 0:
                try:
                    OrderItemOptions.objects.create(
                        order_item=order_item,
                        opt_id=opt_id,
                        level=int(opt_data.get("level", 1)),
                    )
                except Exception:
                    pass

    # 寫入 order-level 選項（辣度、加蒜、九層塔）
    if "辣度" in opts:
        OrderItemOptions.objects.create(
            order=order, opt=opts["辣度"], level=spicy_level
        )
    if extra_garlic_qty > 0 and "加蒜" in opts:
        OrderItemOptions.objects.create(
            order=order, opt=opts["加蒜"], level=extra_garlic_qty
        )
    if extra_basil_qty > 0 and "九層塔" in opts:
        OrderItemOptions.objects.create(
            order=order, opt=opts["九層塔"], level=extra_basil_qty
        )

    request.session["cart"] = []
    messages.success(request, _("訂單 #{pk} 已成功送出！").format(pk=order.pk))
    return redirect("web_app:home")
