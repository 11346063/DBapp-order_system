from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from web_app.models import Order, OrderItem


@login_required
def order_history_view(request):
    if request.user.identity == "A" or request.user.identity == "E":
        return redirect("web_app:staff_orders")

    orders = Order.objects.filter(user=request.user).order_by("-create_time")

    for order in orders:
        order.items = OrderItem.objects.filter(order=order).select_related("menu")

    return render(request, "order_history.html", {"orders": orders})
