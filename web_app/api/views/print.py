"""出單機列印 API：供店內列印代理輪詢待印工作並回報結果。"""

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from web_app.api.permissions import IsEmployee, IsPrintAgent
from web_app.api.utils import api_success
from web_app.constants import CUT_OPTION_ID
from web_app.models import Order
from web_app.services import order as order_service
from web_app.services import printing as printing_service
from web_app.services.exceptions import NotFoundError

_PrintErrorResponse = inline_serializer(
    name="PrintErrorResponse",
    fields={
        "status": serializers.CharField(default="error"),
        "message": serializers.CharField(),
    },
)


def _build_ticket_payload(job):
    """將 PrintJob 的訂單組成代理排版所需的結構化資料。"""
    order = job.order
    items = []
    for item in order.orderitem_set.all():
        opt_labels = []
        for oi in item.orderitemoption_set.all():
            if oi.opt_id == CUT_OPTION_ID:
                opt_labels.append("切" if oi.level == 1 else "不切")
            else:
                opt_labels.append(oi.opt.name)
        items.append(
            {
                "name": item.menu.name,
                "amount": item.amount,
                "options": opt_labels,
                "total_price": item.total_price,
            }
        )
    order_level = [
        o for o in order.orderitemoption_set.all() if o.order_item_id is None
    ]
    return {
        "job_id": job.pk,
        "order_id": order.pk,
        "pickup_code": order.pickup_code,
        "customer_phone": order.customer_phone,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
        "order_options": order_service.format_order_options(order_level),
        "remark": order.remark,
        "items": items,
        "price_total": order.price_total,
    }


class PrintPendingAPIView(APIView):
    permission_classes = [IsPrintAgent]

    @extend_schema(
        summary="取得待印工作（列印代理用）",
        description=(
            "店內列印代理以 `X-Print-Token` header 驗證，輪詢待印出單工作。\n\n"
            "**驗證**：需在 request header 帶入 `X-Print-Token: <token>`。"
        ),
        tags=["出單機"],
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="PrintPendingResponse",
                    fields={
                        "status": serializers.CharField(default="success"),
                        "message": serializers.CharField(default="操作成功"),
                        "data": inline_serializer(
                            name="PrintPendingData",
                            fields={
                                "jobs": serializers.ListField(
                                    child=inline_serializer(
                                        name="PrintJob",
                                        fields={
                                            "job_id": serializers.IntegerField(),
                                            "order_id": serializers.IntegerField(),
                                            "pickup_code": serializers.CharField(),
                                            "customer_phone": serializers.CharField(),
                                            "created_at": serializers.CharField(),
                                            "order_options": serializers.CharField(),
                                            "remark": serializers.CharField(),
                                            "items": serializers.ListField(
                                                child=serializers.DictField()
                                            ),
                                            "price_total": serializers.IntegerField(),
                                        },
                                    ),
                                    help_text="待印工作清單（空陣列表示無工作）",
                                )
                            },
                        ),
                    },
                ),
                description="取得成功，data.jobs 為待印工作清單",
                examples=[
                    OpenApiExample(
                        "無待印工作",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {"jobs": []},
                        },
                    )
                ],
            ),
            403: OpenApiResponse(
                response=_PrintErrorResponse,
                description="X-Print-Token 缺失或不正確",
                examples=[
                    OpenApiExample(
                        "Token 無效",
                        value={
                            "status": "error",
                            "message": "Authentication credentials were not provided.",
                        },
                    )
                ],
            ),
        },
    )
    def get(self, request):
        jobs = printing_service.get_pending_jobs()
        return api_success({"jobs": [_build_ticket_payload(j) for j in jobs]})


class PrintAckAPIView(APIView):
    permission_classes = [IsPrintAgent]

    @extend_schema(
        summary="回報列印結果（列印代理用）",
        description=(
            "代理列印後回報成功/失敗。\n\n"
            '**Request body**：`{"success": bool, "error": "錯誤訊息（選填）"}`\n\n'
            "**驗證**：需在 request header 帶入 `X-Print-Token: <token>`。"
        ),
        tags=["出單機"],
        request=inline_serializer(
            name="PrintAckRequest",
            fields={
                "success": serializers.BooleanField(help_text="列印是否成功"),
                "error": serializers.CharField(
                    required=False, help_text="失敗原因（選填）"
                ),
            },
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="PrintAckResponse",
                    fields={
                        "status": serializers.CharField(default="success"),
                        "message": serializers.CharField(default="操作成功"),
                        "data": inline_serializer(
                            name="PrintAckData",
                            fields={"updated": serializers.BooleanField()},
                        ),
                    },
                ),
                description="回報成功",
                examples=[
                    OpenApiExample(
                        "回報成功",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {"updated": True},
                        },
                    )
                ],
            ),
            403: OpenApiResponse(
                response=_PrintErrorResponse,
                description="X-Print-Token 缺失或不正確",
                examples=[
                    OpenApiExample(
                        "403 範例",
                        value={"status": "error", "message": "X-Print-Token 無效"},
                    )
                ],
            ),
            404: OpenApiResponse(
                response=_PrintErrorResponse,
                description="找不到指定 ID 的列印工作",
                examples=[
                    OpenApiExample(
                        "工作不存在",
                        value={"status": "error", "message": "找不到此列印工作"},
                    )
                ],
            ),
        },
    )
    def post(self, request, pk):
        success = bool(request.data.get("success", True))
        error = request.data.get("error", "")
        found = printing_service.mark_job(pk, success, error)
        if not found:
            return Response(
                {"status": "error", "message": "找不到此列印工作"}, status=404
            )
        return api_success({"updated": True})


class OrderReprintAPIView(APIView):
    permission_classes = [IsEmployee]

    @extend_schema(
        summary="重印訂單出單",
        description=(
            "員工重新建立一筆待印工作，供出單機再次列印。\n\n"
            "**權限**：需員工（`identity=E`）或管理員（`identity=A`）身份，"
            "透過 JWT Bearer Token 驗證。"
        ),
        tags=["出單機"],
        request=None,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="OrderReprintResponse",
                    fields={
                        "status": serializers.CharField(default="success"),
                        "message": serializers.CharField(default="已加入列印佇列"),
                        "data": inline_serializer(
                            name="OrderReprintData",
                            fields={},
                        ),
                    },
                ),
                description="重印工作已成功加入列印佇列",
                examples=[
                    OpenApiExample(
                        "成功",
                        value={
                            "status": "success",
                            "message": "已加入列印佇列",
                            "data": {},
                        },
                    )
                ],
            ),
            401: OpenApiResponse(
                response=_PrintErrorResponse,
                description="未提供有效的 JWT Token 或 Token 已過期",
                examples=[
                    OpenApiExample(
                        "401 範例",
                        value={"status": "error", "message": "請先登入"},
                    )
                ],
            ),
            403: OpenApiResponse(
                response=_PrintErrorResponse,
                description="身份不符（需員工或管理員身份）",
                examples=[
                    OpenApiExample(
                        "403 範例",
                        value={"status": "error", "message": "您沒有執行此操作的權限"},
                    )
                ],
            ),
            404: OpenApiResponse(
                response=_PrintErrorResponse,
                description="找不到指定 ID 的訂單",
                examples=[
                    OpenApiExample(
                        "訂單不存在",
                        value={"status": "error", "message": "找不到此訂單"},
                    )
                ],
            ),
        },
    )
    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist as exc:
            raise NotFoundError("找不到此訂單") from exc
        printing_service.enqueue_print_job(order)
        return api_success({}, message="已加入列印佇列")
