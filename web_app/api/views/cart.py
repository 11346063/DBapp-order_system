from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from web_app.api.serializers.cart import (
    CartAddSerializer,
    CartAdjustSerializer,
    CartRemoveSerializer,
    CartUpdateSerializer,
)
from web_app.api.utils import api_error, api_success

# ---------- 共用 inline schema ----------

_ErrorResponse = inline_serializer(
    name="CartErrorResponse",
    fields={
        "status": serializers.CharField(default="error"),
        "message": serializers.CharField(),
    },
)

_CartCountResponse = inline_serializer(
    name="CartCountResponse",
    fields={
        "status": serializers.CharField(default="success"),
        "message": serializers.CharField(default="操作成功"),
        "data": inline_serializer(
            name="CartCountData",
            fields={"cart_count": serializers.IntegerField(help_text="購物車目前總件數")},
        ),
    },
)

_CartAdjustResponse = inline_serializer(
    name="CartAdjustResponse",
    fields={
        "status": serializers.CharField(default="success"),
        "message": serializers.CharField(default="操作成功"),
        "data": inline_serializer(
            name="CartAdjustData",
            fields={
                "cart_count": serializers.IntegerField(help_text="購物車目前總件數"),
                "item_quantity": serializers.IntegerField(
                    help_text="調整後該品項的數量（已移除則為 0）"
                ),
            },
        ),
    },
)

_CartTotalResponse = inline_serializer(
    name="CartTotalResponse",
    fields={
        "status": serializers.CharField(default="success"),
        "message": serializers.CharField(default="操作成功"),
        "data": inline_serializer(
            name="CartTotalData",
            fields={
                "total": serializers.IntegerField(help_text="購物車所有品項小計加總（元）"),
                "cart_count": serializers.IntegerField(help_text="購物車目前總件數"),
            },
        ),
    },
)

_400_validation = OpenApiResponse(
    response=_ErrorResponse,
    description="欄位驗證失敗，回傳第一個錯誤訊息",
    examples=[
        OpenApiExample(
            "驗證失敗範例",
            value={"status": "error", "message": "price 不可為負數"},
        )
    ],
)


class CartAddAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="加入購物車",
        description=(
            "將指定餐點（含選項）加入 session 購物車。\n\n"
            "購物車以 server-side session 儲存，不寫入資料庫。\n"
            "無需登入即可使用。"
        ),
        tags=["購物車"],
        request=CartAddSerializer,
        responses={
            200: OpenApiResponse(
                response=_CartCountResponse,
                description="加入成功，回傳購物車目前總件數",
                examples=[
                    OpenApiExample(
                        "成功範例",
                        value={"status": "success", "message": "操作成功", "data": {"cart_count": 3}},
                    )
                ],
            ),
            400: _400_validation,
        },
    )
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

    @extend_schema(
        summary="快速調整購物車數量（無選項品項）",
        description=(
            "依 `menu_id` 搜尋購物車中**無選項**的同款品項，以 `delta` 調整數量。\n\n"
            "- `delta` 為正數時加量；為負數時減量。\n"
            "- 數量歸零時自動移除該品項。\n"
            "- 找不到對應品項且調整後數量 > 0 時，自動建立新品項。\n\n"
            "無需登入即可使用。"
        ),
        tags=["購物車"],
        request=CartAdjustSerializer,
        responses={
            200: OpenApiResponse(
                response=_CartAdjustResponse,
                description="調整成功，回傳購物車總件數與該品項最新數量",
                examples=[
                    OpenApiExample(
                        "成功範例",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {"cart_count": 4, "item_quantity": 2},
                        },
                    )
                ],
            ),
            400: _400_validation,
        },
    )
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

    @extend_schema(
        summary="依索引更新購物車品項數量",
        description=(
            "以購物車陣列中的 `index`（從 0 開始）定位品項，直接設定新數量。\n\n"
            "- `quantity <= 0` 時移除該品項。\n"
            "- `index` 超出範圍時不做任何變更（靜默忽略）。\n\n"
            "無需登入即可使用。"
        ),
        tags=["購物車"],
        request=CartUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=_CartTotalResponse,
                description="更新成功，回傳購物車總金額與總件數",
                examples=[
                    OpenApiExample(
                        "成功範例",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {"total": 320, "cart_count": 4},
                        },
                    )
                ],
            ),
            400: _400_validation,
        },
    )
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

    @extend_schema(
        summary="依索引移除購物車品項",
        description=(
            "以購物車陣列中的 `index`（從 0 開始）移除對應品項。\n\n"
            "`index` 超出範圍時不做任何變更（靜默忽略）。\n\n"
            "無需登入即可使用。"
        ),
        tags=["購物車"],
        request=CartRemoveSerializer,
        responses={
            200: OpenApiResponse(
                response=_CartTotalResponse,
                description="移除成功，回傳購物車總金額與總件數",
                examples=[
                    OpenApiExample(
                        "成功範例",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {"total": 160, "cart_count": 2},
                        },
                    )
                ],
            ),
            400: _400_validation,
        },
    )
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
