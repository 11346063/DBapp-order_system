from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from web_app.models import Order, OrderItem, Menu


def payment_view(request):
    if request.user.is_authenticated:
        if request.user.identity in ("A", "E"):
            return redirect("web_app:staff_orders")

    cart = request.session.get("cart", [])
    if not cart:
        messages.warning(request, "購物車是空的")
        return redirect("web_app:home")

    total = sum(item["subtotal"] for item in cart)
    return render(
        request,
        "payment.html",
        {
            "cart_items": cart,
            "total": total,
            "is_guest": not request.user.is_authenticated,
        },
    )


def order_submit(request):
    if request.user.is_authenticated:
        if request.user.identity in ("A", "E"):
            return redirect("web_app:staff_orders")

    if request.method != "POST":
        return redirect("web_app:payment")

    cart = request.session.get("cart", [])
    if not cart:
        messages.warning(request, "購物車是空的")
        return redirect("web_app:home")

    total = sum(item["subtotal"] for item in cart)

    # Generate sno
    last_order = Order.objects.order_by("-sno").first()
    sno = (last_order.sno + 1) if last_order else 1

    remark = request.POST.get("remark", "").strip()[:200]

    order = Order.objects.create(
        sno=sno,
        user=request.user if request.user.is_authenticated else None,
        create_time=timezone.now(),
        status=0,
        price_total=total,
        remark=remark,
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
    messages.success(request, f"訂單 #{sno} 已成功送出！")
    return redirect("web_app:home")
