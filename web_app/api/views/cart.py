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
from rest_framework.response import Response
from rest_framework.views import APIView

from web_app.api.utils import api_success
from web_app.services import cart as cart_service

_CartErrorResponse = inline_serializer(
    name="CartErrorResponse",
    fields={
        "status": serializers.CharField(default="error"),
        "message": serializers.CharField(),
    },
)


class CartValidatePricesAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="驗證購物車價格",
        description=(
            "比對前端 localStorage 購物車內各品項的價格與後端 DB 現值，"
            "回傳有價格異動的品項清單。無需登入即可呼叫。"
        ),
        tags=["購物車"],
        request=inline_serializer(
            name="CartValidateRequest",
            fields={
                "cart": serializers.ListField(
                    child=inline_serializer(
                        name="CartValidateItem",
                        fields={
                            "menu_id": serializers.IntegerField(),
                            "price": serializers.IntegerField(),
                        },
                    ),
                    help_text="前端購物車品項陣列",
                )
            },
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="CartValidateResponse",
                    fields={
                        "status": serializers.CharField(default="success"),
                        "message": serializers.CharField(default="操作成功"),
                        "data": serializers.ListField(
                            child=inline_serializer(
                                name="CartValidateChangedItem",
                                fields={
                                    "menu_id": serializers.IntegerField(),
                                    "old_price": serializers.IntegerField(),
                                    "new_price": serializers.IntegerField(),
                                    "name": serializers.CharField(),
                                },
                            ),
                            help_text="有價格異動的品項清單（空陣列表示無異動）",
                        ),
                    },
                ),
                description="驗證完成，data 為有異動的品項清單（空陣列表示全部一致）",
                examples=[
                    OpenApiExample(
                        "無異動",
                        value={"status": "success", "message": "操作成功", "data": []},
                    ),
                    OpenApiExample(
                        "有品項漲價",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": [
                                {
                                    "menu_id": 3,
                                    "old_price": 80,
                                    "new_price": 90,
                                    "name": "雞排",
                                }
                            ],
                        },
                    ),
                ],
            ),
            400: OpenApiResponse(
                response=_CartErrorResponse,
                description="請求格式錯誤（cart 欄位缺失或格式不正確）",
                examples=[
                    OpenApiExample(
                        "格式錯誤",
                        value={"status": "error", "message": "cart 格式不正確"},
                    )
                ],
            ),
        },
    )
    def post(self, request):
        cart = request.data.get("cart")
        if not isinstance(cart, list):
            return Response(
                {"status": "error", "message": "cart 格式不正確"}, status=400
            )
        return api_success(cart_service.validate_prices_for_cart(cart))


@method_decorator(csrf_protect, name="dispatch")
class CartSyncPricesAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="同步購物車價格",
        description=(
            "將前端 localStorage 購物車內各品項的價格更新為後端 DB 現值，"
            "回傳同步後的完整購物車、總金額與品項數量。無需登入即可呼叫。\n\n"
            "⚠️ 此端點受 CSRF 保護，需帶入有效 CSRF Token。"
        ),
        tags=["購物車"],
        request=inline_serializer(
            name="CartSyncRequest",
            fields={
                "cart": serializers.ListField(
                    child=inline_serializer(
                        name="CartSyncItem",
                        fields={
                            "menu_id": serializers.IntegerField(),
                            "price": serializers.IntegerField(),
                            "amount": serializers.IntegerField(),
                        },
                    ),
                    help_text="前端購物車品項陣列",
                )
            },
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="CartSyncResponse",
                    fields={
                        "status": serializers.CharField(default="success"),
                        "message": serializers.CharField(default="操作成功"),
                        "data": inline_serializer(
                            name="CartSyncData",
                            fields={
                                "cart": serializers.ListField(
                                    child=serializers.DictField(),
                                    help_text="同步後的購物車品項陣列",
                                ),
                                "total": serializers.IntegerField(help_text="總金額"),
                                "cart_count": serializers.IntegerField(
                                    help_text="總品項數量"
                                ),
                            },
                        ),
                    },
                ),
                description="同步成功，回傳更新後的購物車資料",
                examples=[
                    OpenApiExample(
                        "同步成功",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {
                                "cart": [{"menu_id": 1, "price": 90, "amount": 2}],
                                "total": 180,
                                "cart_count": 2,
                            },
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                response=_CartErrorResponse,
                description="請求格式錯誤（cart 欄位缺失或格式不正確）",
                examples=[
                    OpenApiExample(
                        "格式錯誤",
                        value={"status": "error", "message": "cart 格式不正確"},
                    )
                ],
            ),
        },
    )
    def post(self, request):
        cart = request.data.get("cart")
        if not isinstance(cart, list):
            return Response(
                {"status": "error", "message": "cart 格式不正確"}, status=400
            )
        updated = cart_service.sync_prices_for_cart(cart)
        return api_success(
            {
                "cart": updated,
                "total": cart_service.cart_total(updated),
                "cart_count": cart_service.cart_count(updated),
            }
        )
