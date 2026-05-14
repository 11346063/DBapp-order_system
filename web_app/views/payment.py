from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext as _
from web_app.models import Identity, Order, OrderItem, Menu


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

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        create_time=timezone.now(),
        status=0,
        price_total=total,
        remark=remark,
        customer_phone=customer_phone if is_staff_order else "",
    )

    for item in cart:
        try:
            menu = Menu.objects.get(pk=item["menu_id"])
            OrderItem.objects.create(
                order=order,
                menu=menu,
                amount=item["quantity"],
                total_price=item["subtotal"],
            )
        except Menu.DoesNotExist:
            continue

    request.session["cart"] = []
    messages.success(request, _("訂單 #{pk} 已成功送出！").format(pk=order.pk))
    return redirect("web_app:home")
