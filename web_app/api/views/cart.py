from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
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
    CartRemoveByMenuSerializer,
    CartRemoveSerializer,
    CartUpdateSerializer,
)
from web_app.api.utils import api_success
from web_app.services import cart as cart_service

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
            fields={
                "cart_count": serializers.IntegerField(help_text="購物車目前總件數")
            },
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
                "total": serializers.IntegerField(
                    help_text="購物車所有品項小計加總（元）"
                ),
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


class CartDetailAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="取得購物車內容",
        description="回傳目前購物車明細、總金額、總件數與價格異動狀態。",
        tags=["購物車"],
    )
    def get(self, request):
        cart = cart_service.get_cart(request.user, request.session)
        price_status = cart_service.validate_prices(request.user, request.session)
        return api_success(
            {
                "items": cart,
                "total": cart_service.cart_total(cart),
                "cart_count": cart_service.cart_count(cart),
                "price_changes": price_status["price_changes"],
            }
        )


class CartValidatePricesAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="檢查購物車價格是否異動",
        description="只檢查最新菜單/選項價格，不修改購物車資料。",
        tags=["購物車"],
    )
    def post(self, request):
        return api_success(cart_service.validate_prices(request.user, request.session))


@method_decorator(csrf_protect, name="dispatch")
class CartMutationAPIView(APIView):
    permission_classes = [AllowAny]


class CartSyncPricesAPIView(CartMutationAPIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="同步購物車為最新價格",
        description="顧客接受最新價格後，更新購物車價格 snapshot 與小計。",
        tags=["購物車"],
    )
    def post(self, request):
        return api_success(cart_service.sync_prices(request.user, request.session))


class CartAddAPIView(CartMutationAPIView):
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
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {"cart_count": 3},
                        },
                    )
                ],
            ),
            400: _400_validation,
        },
    )
    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_success(
            cart_service.add_item(
                request.user,
                request.session,
                serializer.validated_data,
            )
        )


class CartAdjustAPIView(CartMutationAPIView):
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
        serializer.is_valid(raise_exception=True)
        return api_success(
            cart_service.adjust_item(
                request.user,
                request.session,
                serializer.validated_data,
            )
        )


class CartUpdateAPIView(CartMutationAPIView):
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
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        return api_success(
            cart_service.update_item_quantity(
                request.user,
                request.session,
                d["index"],
                d["quantity"],
            )
        )


class CartRemoveAPIView(CartMutationAPIView):
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
        serializer.is_valid(raise_exception=True)
        return api_success(
            cart_service.remove_item(
                request.user,
                request.session,
                serializer.validated_data["index"],
            )
        )


class CartRemoveByMenuAPIView(CartMutationAPIView):
    """依 menu_id 移除購物車中最後一筆該品項（不限選項），用於代客點餐減量。"""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="依 menu_id 移除最後一筆購物車品項",
        description=(
            "在購物車中找最後一筆 `menu_id` 相符的品項並移除（無論有無選項）。\n\n"
            "主要供代客點餐頁的 − 按鈕使用。"
        ),
        tags=["購物車"],
        request=CartRemoveByMenuSerializer,
        responses={
            200: OpenApiResponse(
                response=_CartAdjustResponse,
                description="移除成功，回傳購物車總件數與該品項剩餘總數量",
            ),
            400: _400_validation,
        },
    )
    def post(self, request):
        serializer = CartRemoveByMenuSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_success(
            cart_service.remove_last_item_by_menu(
                request.user,
                request.session,
                serializer.validated_data["menu_id"],
            )
        )
