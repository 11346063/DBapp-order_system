from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from web_app.api.permissions import IsEmployee
from web_app.api.serializers.order import OrderStatusSerializer, ReorderSerializer
from web_app.api.utils import api_error, api_success
from web_app.models import Menu, Order, OrderItem


def _order_status_counts():
    return {
        0: Order.objects.filter(status=0).count(),
        1: Order.objects.filter(status=1).count(),
        2: Order.objects.filter(status=2).count(),
    }


class OrderStatusAPIView(APIView):
    permission_classes = [IsEmployee]

    def post(self, request, pk):
        return self.patch(request, pk)

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = OrderStatusSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return api_error(str(first_error))

        order.status = serializer.validated_data["status"]
        order.save(update_fields=["status"])
        return api_success({"status_counts": _order_status_counts()})


class ReorderAPIView(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return api_error("請先登入", status=401)
        if request.user.identity in ("A", "E"):
            return api_error("員工不能使用再次訂購", status=403)

        serializer = ReorderSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return api_error(str(first_error))

        order = get_object_or_404(Order, pk=serializer.validated_data["order_id"], user=request.user)
        items = OrderItem.objects.filter(order=order).select_related("menu")

        cart = request.session.get("cart", [])
        added = 0
        for item in items:
            try:
                menu = item.menu
                cart.append(
                    {
                        "menu_id": menu.pk,
                        "name": menu.name,
                        "base_price": menu.price,
                        "options": [],
                        "options_price": 0,
                        "unit_price": menu.price,
                        "quantity": item.amount,
                        "subtotal": menu.price * item.amount,
                    }
                )
                added += item.amount
            except Menu.DoesNotExist:
                continue

        request.session["cart"] = cart
        cart_count = sum(i["quantity"] for i in cart)
        return api_success({"added": added, "cart_count": cart_count})
