from django.db import models
from django.utils import timezone

from web_app.enums import OrderStatus


class Order(models.Model):
    OrderStatus = OrderStatus

    user = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.IntegerField(
        choices=OrderStatus.choices, default=OrderStatus.SUBMITTED
    )
    price_total = models.IntegerField()
    remark = models.CharField(max_length=200, blank=True, default="")
    customer_phone = models.CharField(max_length=20, blank=True, default="")
    ready_at = models.DateTimeField(null=True, blank=True)
    ready_notified_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    estimated_wait_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=200, blank=True, default="")
    pickup_code = models.CharField(max_length=12, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["customer_phone"], name="order_customer_phone_idx"),
            models.Index(
                fields=["status", "created_at"], name="order_status_created_idx"
            ),
        ]
