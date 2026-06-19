"""出單列印工作管理。

雲端負責產生 PrintJob 與提供資料；實際送印由店內列印代理（輪詢 API）執行。
本模組只做純 model 操作，不匯入 order service，避免循環匯入。
"""

from django.db.models import Prefetch
from django.utils import timezone

from web_app.models import OrderItem, OrderItemOption, PrintJob


def enqueue_print_job(order) -> PrintJob:
    """為訂單建立一筆待印工作。"""
    return PrintJob.objects.create(order=order, status=PrintJob.Status.PENDING)


def get_pending_jobs():
    """取得所有待印工作（含已 prefetch 的訂單品項與選項，避免 N+1）。"""
    return list(
        PrintJob.objects.filter(status=PrintJob.Status.PENDING)
        .select_related("order")
        .prefetch_related(
            Prefetch(
                "order__orderitem_set",
                queryset=OrderItem.objects.select_related("menu").prefetch_related(
                    Prefetch(
                        "orderitemoption_set",
                        queryset=OrderItemOption.objects.select_related("opt"),
                    )
                ),
            ),
            Prefetch(
                "order__orderitemoption_set",
                queryset=OrderItemOption.objects.select_related("opt"),
            ),
        )
        .order_by("created_at")
    )


def mark_job(job_id: int, success: bool, error: str = "") -> bool:
    """回報列印結果；找不到工作回傳 False。"""
    try:
        job = PrintJob.objects.get(pk=job_id)
    except PrintJob.DoesNotExist:
        return False
    if success:
        job.status = PrintJob.Status.PRINTED
        job.printed_at = timezone.now()
        job.error = ""
    else:
        job.status = PrintJob.Status.FAILED
        job.error = (error or "")[:255]
    job.save(update_fields=["status", "printed_at", "error"])
    return True
