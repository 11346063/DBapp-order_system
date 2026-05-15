from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from web_app.api.serializers.cart import (
    CartAddSerializer,
    CartAdjustSerializer,
    CartRemoveSerializer,
    CartUpdateSerializer,
)
from web_app.api.utils import api_error, api_success


class CartAddAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return api_error(str(first_error))

        d = serializer.validated_data
        cart = request.session.get("cart", [])

        options_price = sum(opt.get("price", 0) for opt in d["options"])
        unit_price = d["price"] + options_price
        subtotal = unit_price * d["quantity"]

        cart.append(
            {
                "menu_id": d["menu_id"],
                "name": d["name"],
                "base_price": d["price"],
                "options": d["options"],
                "options_price": options_price,
                "unit_price": unit_price,
                "quantity": d["quantity"],
                "subtotal": subtotal,
            }
        )

        request.session["cart"] = cart
        cart_count = sum(item["quantity"] for item in cart)
        return api_success({"cart_count": cart_count})


class CartAdjustAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CartAdjustSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return api_error(str(first_error))

        d = serializer.validated_data
        cart = request.session.get("cart", [])

        target_index = None
        item_quantity = 0
        for index, item in enumerate(cart):
            if item.get("menu_id") == d["menu_id"] and item.get("options", []) == []:
                target_index = index
                item_quantity = item["quantity"]
                break

        item_quantity = max(0, item_quantity + d["delta"])

        if target_index is None and item_quantity > 0:
            cart.append(
                {
                    "menu_id": d["menu_id"],
                    "name": d["name"],
                    "base_price": d["price"],
                    "options": [],
                    "options_price": 0,
                    "unit_price": d["price"],
                    "quantity": item_quantity,
                    "subtotal": d["price"] * item_quantity,
                }
            )
        elif target_index is not None and item_quantity <= 0:
            cart.pop(target_index)
        elif target_index is not None:
            cart[target_index]["quantity"] = item_quantity
            cart[target_index]["subtotal"] = (
                cart[target_index]["unit_price"] * item_quantity
            )

        request.session["cart"] = cart
        cart_count = sum(item["quantity"] for item in cart)
        return api_success({"cart_count": cart_count, "item_quantity": item_quantity})


class CartUpdateAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CartUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return api_error(str(first_error))

        d = serializer.validated_data
        cart = request.session.get("cart", [])

        if 0 <= d["index"] < len(cart):
            if d["quantity"] <= 0:
                cart.pop(d["index"])
            else:
                cart[d["index"]]["quantity"] = d["quantity"]
                cart[d["index"]]["subtotal"] = (
                    cart[d["index"]]["unit_price"] * d["quantity"]
                )

        request.session["cart"] = cart
        total = sum(item["subtotal"] for item in cart)
        cart_count = sum(item["quantity"] for item in cart)
        return api_success({"total": total, "cart_count": cart_count})


class CartRemoveAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CartRemoveSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return api_error(str(first_error))

        d = serializer.validated_data
        cart = request.session.get("cart", [])

        if 0 <= d["index"] < len(cart):
            cart.pop(d["index"])

        request.session["cart"] = cart
        total = sum(item["subtotal"] for item in cart)
        cart_count = sum(item["quantity"] for item in cart)
        return api_success({"total": total, "cart_count": cart_count})
