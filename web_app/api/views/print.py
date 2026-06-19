"""出單機列印 API：供店內列印代理輪詢待印工作並回報結果。"""

from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from web_app.api.permissions import IsEmployee, IsPrintAgent
from web_app.api.utils import api_success
from web_app.models import Order
from web_app.services import order as order_service
from web_app.services import printing as printing_service
from web_app.services import store_settings as settings_service
from web_app.services.exceptions import NotFoundError


def _build_ticket_payload(job, s):
    """將 PrintJob 的訂單組成代理排版所需的結構化資料。"""
    order = job.order
    items = []
    for item in order.orderitem_set.all():
        opt_labels = []
        for oi in item.orderitemoption_set.all():
            if oi.opt.name == s.option_name_cut:
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
        "order_options": order_service.format_order_options(order_level, s),
        "remark": order.remark,
        "items": items,
        "price_total": order.price_total,
    }


class PrintPendingAPIView(APIView):
    permission_classes = [IsPrintAgent]

    @extend_schema(
        summary="取得待印工作（列印代理用）",
        description="店內列印代理以 `X-Print-Token` header 驗證，輪詢待印出單工作。",
        tags=["出單機"],
    )
    def get(self, request):
        s = settings_service.get_settings()
        jobs = printing_service.get_pending_jobs()
        return api_success({"jobs": [_build_ticket_payload(j, s) for j in jobs]})


class PrintAckAPIView(APIView):
    permission_classes = [IsPrintAgent]

    @extend_schema(
        summary="回報列印結果（列印代理用）",
        description="代理列印後回報成功/失敗。body：`{success: bool, error?: str}`。",
        tags=["出單機"],
    )
    def post(self, request, pk):
        success = bool(request.data.get("success", True))
        error = request.data.get("error", "")
        found = printing_service.mark_job(pk, success, error)
        if not found:
            return api_success({"updated": False}, message="找不到此列印工作")
        return api_success({"updated": True})


class OrderReprintAPIView(APIView):
    permission_classes = [IsEmployee]

    @extend_schema(
        summary="重印訂單出單",
        description="員工重新建立一筆待印工作，供出單機再次列印。",
        tags=["出單機"],
    )
    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist as exc:
            raise NotFoundError("找不到此訂單") from exc
        printing_service.enqueue_print_job(order)
        return api_success({}, message="已加入列印佇列")
