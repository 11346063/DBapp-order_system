from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from web_app.api.utils import api_success
from web_app.services import cart as cart_service


class CartValidatePricesAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        cart = request.data.get("cart", [])
        return api_success(cart_service.validate_prices_for_cart(cart))


@method_decorator(csrf_protect, name="dispatch")
class CartSyncPricesAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        cart = request.data.get("cart", [])
        updated = cart_service.sync_prices_for_cart(cart)
        return api_success(
            {
                "cart": updated,
                "total": cart_service.cart_total(updated),
                "cart_count": cart_service.cart_count(updated),
            }
        )
