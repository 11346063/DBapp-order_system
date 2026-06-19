from django.db import models


class PrintJob(models.Model):
    """出單列印工作。由店內列印代理輪詢並送至 ESC/POS 出單機。"""

    class Status(models.IntegerChoices):
        PENDING = 0, "待印"
        PRINTED = 1, "已印"
        FAILED = 2, "失敗"

    order = models.ForeignKey("Order", on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    printed_at = models.DateTimeField(null=True, blank=True)
    error = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]
