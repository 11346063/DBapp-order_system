from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.views import APIView

from web_app.api.permissions import IsCustomer, IsEmployee
from web_app.api.serializers.order import OrderStatusSerializer, ReorderSerializer
from web_app.api.utils import api_error, api_success
from web_app.services import order as order_service
from web_app.services.exceptions import NotFoundError

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
                        "1": serializers.IntegerField(help_text="已完成訂單數量"),
                        "2": serializers.IntegerField(help_text="已取消訂單數量"),
                        "3": serializers.IntegerField(help_text="可取餐訂單數量"),
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
                    "data": {"status_counts": {"0": 3, "1": 2, "2": 1, "3": 4}},
                },
            )
        ],
    ),
    400: OpenApiResponse(
        response=_ErrorResponse,
        description="`status` 值不在允許範圍（0、1、2、3）",
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


class OrderStatusAPIView(APIView):
    permission_classes = [IsEmployee]

    @extend_schema(
        summary="更新訂單狀態（POST 別名）",
        description=(
            "與 PATCH 行為相同，保留供前端相容。\n\n"
            "**權限**：需員工（`identity=E`）或管理員（`identity=A`）身份。\n\n"
            "訂單狀態對照：\n"
            "- `0` — 待處理\n"
            "- `1` — 完成\n"
            "- `2` — 取消\n"
            "- `3` — 可取餐"
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
            "- `1` — 完成\n"
            "- `2` — 取消\n"
            "- `3` — 可取餐"
        ),
        tags=["訂單"],
        request=OrderStatusSerializer,
        responses=_status_update_responses,
    )
    def patch(self, request, pk):
        serializer = OrderStatusSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return api_error(str(first_error))

        try:
            return api_success(
                order_service.update_order_status(
                    pk,
                    serializer.validated_data["status"],
                )
            )
        except NotFoundError as exc:
            return api_error(exc.message, status=exc.status_code)


class OrderReadyAPIView(APIView):
    permission_classes = [IsEmployee]

    @extend_schema(
        summary="通知顧客取餐",
        description=(
            "將指定訂單標記為可取餐，並寫入 `ready_at` 與 `ready_notified_at`。"
            "第一版通知以站內狀態顯示為主。"
        ),
        tags=["訂單"],
        request=None,
        responses=_status_update_responses,
    )
    def post(self, request, pk):
        try:
            return api_success(order_service.mark_order_ready(pk))
        except NotFoundError as exc:
            return api_error(exc.message, status=exc.status_code)


class ReorderAPIView(APIView):
    permission_classes = [IsCustomer]

    @extend_schema(
        summary="再次訂購（複製歷史訂單至購物車）",
        description=(
            "將指定歷史訂單的所有品項（**不含原選項**）加入目前 session 的購物車。\n\n"
            "**權限**：僅限已登入的**顧客**（`identity=C`）使用。\n"
            "- 未登入或非顧客 => `403`\n"
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
            403: OpenApiResponse(
                response=_ErrorResponse,
                description="未登入或非顧客帳號（員工／管理員）",
            ),
            404: OpenApiResponse(
                response=_ErrorResponse,
                description="訂單不存在，或該訂單不屬於目前登入的使用者",
            ),
        },
    )
    def post(self, request):
        serializer = ReorderSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return api_error(str(first_error))

        try:
            result = order_service.reorder_to_cart(
                request.user,
                request.session,
                serializer.validated_data["order_id"],
            )
        except NotFoundError as exc:
            return api_error(exc.message, status=exc.status_code)

        return api_success(result)
