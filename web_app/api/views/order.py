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

from web_app.api.permissions import IsCustomer, IsEmployee
from web_app.api.serializers.order import (
    AcceptOrderSerializer,
    OrderStatusSerializer,
    ReorderSerializer,
    StaffOrderCreateSerializer,
)
from web_app.api.utils import api_error, api_success
from web_app.models.order import Order
from web_app.services import order as order_service
from web_app.services.exceptions import (
    EmptyCartError,
    StaffCustomerPhoneRequired,
    ValidationServiceError,
)

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
                        "0": serializers.IntegerField(help_text="等待接單訂單數量"),
                        "1": serializers.IntegerField(help_text="備餐中訂單數量"),
                        "2": serializers.IntegerField(help_text="可取餐訂單數量"),
                        "3": serializers.IntegerField(help_text="已完成訂單數量"),
                        "4": serializers.IntegerField(help_text="已取消訂單數量"),
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
                    "data": {"status_counts": {"0": 2, "1": 1, "2": 1, "3": 3, "4": 1}},
                },
            )
        ],
    ),
    400: OpenApiResponse(
        response=_ErrorResponse,
        description="`status` 值不在允許範圍（3、4）",
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
            "此端點僅允許設定終止狀態：3=已完成、4=已取消。"
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
            "此端點僅允許設定：3=已完成、4=已取消。"
        ),
        tags=["訂單"],
        request=OrderStatusSerializer,
        responses=_status_update_responses,
    )
    def patch(self, request, pk):
        serializer = OrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_success(
            order_service.update_order_status(
                pk,
                serializer.validated_data["status"],
            )
        )


class OrderReadyAPIView(APIView):
    permission_classes = [IsEmployee]

    @extend_schema(
        summary="通知顧客取餐",
        description=(
            "將備餐中（ACCEPTED）的訂單標記為可取餐，寫入 `ready_at` 與 `ready_notified_at`。"
        ),
        tags=["訂單"],
        request=None,
        responses=_status_update_responses,
    )
    def post(self, request, pk):
        return api_success(order_service.mark_order_ready(pk))


_AcceptSuccessResponse = inline_serializer(
    name="AcceptOrderSuccessResponse",
    fields={
        "status": serializers.CharField(default="success"),
        "message": serializers.CharField(default="接單成功"),
        "data": inline_serializer(
            name="AcceptOrderData",
            fields={
                "order_id": serializers.IntegerField(),
                "status": serializers.IntegerField(help_text="1=備餐中"),
                "estimated_wait_minutes": serializers.IntegerField(),
                "accepted_at": serializers.CharField(),
                "pickup_code": serializers.CharField(),
                "status_counts": inline_serializer(
                    name="AcceptStatusCounts",
                    fields={
                        "0": serializers.IntegerField(),
                        "1": serializers.IntegerField(),
                        "2": serializers.IntegerField(),
                        "3": serializers.IntegerField(),
                        "4": serializers.IntegerField(),
                    },
                ),
            },
        ),
    },
)


class OrderAcceptAPIView(APIView):
    permission_classes = [IsEmployee]

    @extend_schema(
        summary="員工接單",
        description=(
            "將等待接單（SUBMITTED）的訂單轉為備餐中（ACCEPTED），"
            "並記錄接單員工、等待時間與取餐號碼。"
        ),
        tags=["訂單"],
        request=AcceptOrderSerializer,
        responses={
            200: OpenApiResponse(
                response=_AcceptSuccessResponse, description="接單成功"
            ),
            400: OpenApiResponse(
                response=_ErrorResponse, description="驗證失敗或訂單非等待接單狀態"
            ),
            403: OpenApiResponse(
                response=_ErrorResponse, description="需員工或管理員身份"
            ),
            404: OpenApiResponse(response=_ErrorResponse, description="找不到訂單"),
        },
    )
    def post(self, request, pk):
        serializer = AcceptOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = order_service.accept_order(
            pk,
            request.user,
            serializer.validated_data["estimated_wait_minutes"],
        )
        return api_success(result, message="接單成功")


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
        serializer.is_valid(raise_exception=True)
        result = order_service.reorder_to_cart(
            request.user,
            request.session,
            serializer.validated_data["order_id"],
        )
        return api_success(result)


class OrderCustomerStatusAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="顧客查詢訂單狀態（Polling 用）",
        description=(
            "讓顧客（含訪客）在等待頁輪詢訂單狀態。\n\n"
            "驗證規則：登入顧客需為訂單擁有者；訪客需在 session 中持有此訂單 ID。"
        ),
        tags=["訂單"],
        responses={
            200: inline_serializer(
                name="CustomerOrderStatusResponse",
                fields={
                    "status": serializers.CharField(default="success"),
                    "data": inline_serializer(
                        name="CustomerOrderStatusData",
                        fields={
                            "order_status": serializers.IntegerField(),
                            "estimated_wait_minutes": serializers.IntegerField(
                                allow_null=True
                            ),
                            "pickup_code": serializers.CharField(),
                        },
                    ),
                },
            ),
            403: OpenApiResponse(
                response=_ErrorResponse, description="無權限查詢此訂單"
            ),
            404: OpenApiResponse(response=_ErrorResponse, description="訂單不存在"),
        },
    )
    def get(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"status": "error", "message": "找不到此訂單"}, status=404)

        if request.user.is_authenticated:
            if order.user_id != request.user.pk:
                return Response(
                    {"status": "error", "message": "無權限查詢此訂單"}, status=403
                )
        else:
            if request.session.get("last_order_id") != pk:
                return Response(
                    {"status": "error", "message": "無權限查詢此訂單"}, status=403
                )

        return api_success(
            {
                "order_status": order.status,
                "estimated_wait_minutes": order.estimated_wait_minutes,
                "pickup_code": order.pickup_code,
            }
        )


class StaffOrderCreateAPIView(APIView):
    permission_classes = [IsEmployee]

    @extend_schema(
        summary="員工代客建立訂單（直接接單）",
        description="員工不經購物車直接建立代客訂單，自動設為備餐中（ACCEPTED）。",
        tags=["訂單"],
        request=StaffOrderCreateSerializer,
        responses={
            200: inline_serializer(
                name="StaffOrderCreateResponse",
                fields={
                    "status": serializers.CharField(default="success"),
                    "message": serializers.CharField(
                        default="代客訂單已送出，已自動接單"
                    ),
                    "data": inline_serializer(
                        name="StaffOrderCreateData",
                        fields={"order_id": serializers.IntegerField()},
                    ),
                },
            ),
            400: OpenApiResponse(response=_ErrorResponse, description="缺少電話或品項"),
        },
    )
    def post(self, request):
        serializer = StaffOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = order_service.create_staff_order_from_items(
                request.user, serializer.validated_data
            )
        except StaffCustomerPhoneRequired as exc:
            return api_error(exc.message)
        except EmptyCartError as exc:
            return api_error(exc.message)
        except ValidationServiceError as exc:
            return api_error(exc.message)
        return api_success({"order_id": order.pk}, message="代客訂單已送出，已自動接單")
