from django.db.models import Prefetch
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from web_app.models import Identity, Order, OrderItem


@login_required
def order_history_view(request):
    if request.user.identity in (Identity.ADMIN, Identity.EMPLOYEE):
        return redirect("web_app:staff_orders")

    # Prefetch 取代 for-loop 內的 N 次查詢，整體只剩 2 次 DB hit
    orders = list(
        Order.objects.filter(user=request.user)
        .prefetch_related(
            Prefetch(
                "orderitem_set",
                queryset=OrderItem.objects.select_related("menu"),
                to_attr="items",
            )
        )
        .order_by("-created_at")
    )

    return render(request, "order_history.html", {"orders": orders})
