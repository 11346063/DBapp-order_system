from django.db import models
from django.utils import timezone


class Order(models.Model):
    class OrderStatus(models.IntegerChoices):
        PENDING = 0, "等待中"
        COMPLETED = 1, "已完成"
        CANCELLED = 2, "已取消"
        READY = 3, "可取餐"

    user = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.IntegerField(
        choices=OrderStatus.choices, default=OrderStatus.PENDING
    )
    price_total = models.IntegerField()
    remark = models.CharField(max_length=200, blank=True, default="")
    customer_phone = models.CharField(max_length=20, blank=True, default="")
    ready_at = models.DateTimeField(null=True, blank=True)
    ready_notified_at = models.DateTimeField(null=True, blank=True)
