from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.views import APIView

from web_app.api.permissions import IsEmployee
from web_app.api.serializers.order import OrderStatusSerializer, ReorderSerializer
from web_app.api.utils import api_error, api_success
from web_app.models import Menu, Order, OrderItem

# ---------- 共用 inline schema ----------

_ErrorResponse = inline_serializer(
    name="OrderErrorResponse",
    fields={
        "status": serializers.CharField(default="error"),
        "message": serializers.CharField(),
    },
)

_OrderStatusSuccessResponse = inline_serializer(
    name="OrderStatusSuccessResponse",
    fields={
        "status": serializers.CharField(default="success"),
        "message": serializers.CharField(default="操作成功"),
        "data": inline_serializer(
            name="OrderStatusData",
            fields={
                "status_counts": inline_serializer(
                    name="StatusCounts",
                    fields={
                        "0": serializers.IntegerField(help_text="待處理訂單數量"),
                        "1": serializers.IntegerField(help_text="備餐中訂單數量"),
                        "2": serializers.IntegerField(help_text="已完成訂單數量"),
                    },
                )
            },
        ),
    },
)

_ReorderSuccessResponse = inline_serializer(
    name="ReorderSuccessResponse",
    fields={
        "status": serializers.CharField(default="success"),
        "message": serializers.CharField(default="操作成功"),
        "data": inline_serializer(
            name="ReorderData",
            fields={
                "added": serializers.IntegerField(help_text="本次加入購物車的總件數"),
                "cart_count": serializers.IntegerField(help_text="購物車目前總件數"),
            },
        ),
    },
)

_status_update_responses = {
    200: OpenApiResponse(
        response=_OrderStatusSuccessResponse,
        description="狀態更新成功，回傳各狀態的訂單數量統計",
        examples=[
            OpenApiExample(
                "成功範例",
                value={
                    "status": "success",
                    "message": "操作成功",
                    "data": {"status_counts": {"0": 3, "1": 2, "2": 10}},
                },
            )
        ],
    ),
    400: OpenApiResponse(
        response=_ErrorResponse,
        description="`status` 值不在允許範圍（0、1、2）",
        examples=[
            OpenApiExample(
                "無效狀態值",
                value={"status": "error", "message": '"5" is not a valid choice.'},
            )
        ],
    ),
    401: OpenApiResponse(
        response=_ErrorResponse,
        description="未提供有效的 JWT Token 或 Token 已過期",
    ),
    403: OpenApiResponse(
        response=_ErrorResponse,
        description="身份不符（需員工或管理員身份，`identity=E` 或 `identity=A`）",
    ),
    404: OpenApiResponse(
        response=_ErrorResponse,
        description="找不到指定 ID 的訂單",
        examples=[
            OpenApiExample(
                "404 範例",
                value={"status": "error", "message": "找不到此訂單"},
            )
        ],
    ),
}


def _order_status_counts():
    return {
        0: Order.objects.filter(status=0).count(),
        1: Order.objects.filter(status=1).count(),
        2: Order.objects.filter(status=2).count(),
    }


class OrderStatusAPIView(APIView):
    permission_classes = [IsEmployee]

    @extend_schema(
        summary="更新訂單狀態（POST 別名）",
        description=(
            "與 PATCH 行為相同，保留供前端相容。\n\n"
            "**權限**：需員工（`identity=E`）或管理員（`identity=A`）身份。\n\n"
            "訂單狀態對照：\n"
            "- `0` — 待處理\n"
            "- `1` — 備餐中\n"
            "- `2` — 完成"
        ),
        tags=["訂單"],
        request=OrderStatusSerializer,
        responses=_status_update_responses,
    )
    def post(self, request, pk):
        return self.patch(request, pk)

    @extend_schema(
        summary="更新訂單狀態",
        description=(
            "將指定訂單的狀態更新為新值，並回傳目前全部狀態的訂單數量統計（供前端即時刷新）。\n\n"
            "**權限**：需員工（`identity=E`）或管理員（`identity=A`）身份。\n\n"
            "訂單狀態對照：\n"
            "- `0` — 待處理\n"
            "- `1` — 備餐中\n"
            "- `2` — 完成"
        ),
        tags=["訂單"],
        request=OrderStatusSerializer,
        responses=_status_update_responses,
    )
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
    @extend_schema(
        summary="再次訂購（複製歷史訂單至購物車）",
        description=(
            "將指定歷史訂單的所有品項（**不含原選項**）加入目前 session 的購物車。\n\n"
            "**權限**：僅限已登入的**顧客**（`identity=C`）使用。\n"
            "- 未登入 => `401`\n"
            "- 員工或管理員登入 => `403`\n"
            "- 訂單不存在或不屬於目前使用者 => `404`\n\n"
            "若訂單中某品項對應的菜單已被刪除，該品項會被跳過（不會中斷整個流程）。"
        ),
        tags=["訂單"],
        request=ReorderSerializer,
        responses={
            200: OpenApiResponse(
                response=_ReorderSuccessResponse,
                description="再次訂購成功，回傳加入的件數與購物車總件數",
                examples=[
                    OpenApiExample(
                        "成功範例",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {"added": 3, "cart_count": 5},
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                response=_ErrorResponse,
                description="`order_id` 格式錯誤（非整數）",
                examples=[
                    OpenApiExample(
                        "格式錯誤",
                        value={
                            "status": "error",
                            "message": "A valid integer is required.",
                        },
                    )
                ],
            ),
            401: OpenApiResponse(
                response=_ErrorResponse,
                description="未登入或 session 已過期",
                examples=[
                    OpenApiExample(
                        "未登入",
                        value={"status": "error", "message": "請先登入"},
                    )
                ],
            ),
            403: OpenApiResponse(
                response=_ErrorResponse,
                description="員工或管理員帳號不允許使用此功能",
                examples=[
                    OpenApiExample(
                        "員工禁用",
                        value={"status": "error", "message": "員工不能使用再次訂購"},
                    )
                ],
            ),
            404: OpenApiResponse(
                response=_ErrorResponse,
                description="訂單不存在，或該訂單不屬於目前登入的使用者",
            ),
        },
    )
    def post(self, request):
        if not request.user.is_authenticated:
            return api_error("請先登入", status=401)
        if request.user.identity in ("A", "E"):
            return api_error("員工不能使用再次訂購", status=403)

        serializer = ReorderSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return api_error(str(first_error))

        order = get_object_or_404(
            Order, pk=serializer.validated_data["order_id"], user=request.user
        )
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
