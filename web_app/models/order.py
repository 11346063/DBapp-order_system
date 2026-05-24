from django.db import models
from django.utils import timezone


class Order(models.Model):
    class OrderStatus(models.IntegerChoices):
        SUBMITTED = 0, "等待接單"
        ACCEPTED = 1, "備餐中"
        READY = 2, "可取餐"
        COMPLETED = 3, "已完成"
        CANCELLED = 4, "已取消"

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
    accepted_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_orders",
    )
    estimated_wait_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=200, blank=True, default="")
    pickup_code = models.CharField(max_length=12, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["customer_phone"], name="order_customer_phone_idx"),
        ]
