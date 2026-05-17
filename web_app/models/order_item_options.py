from django.db import models


class OrderItemOptions(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE, null=True, blank=True)
    order_item = models.ForeignKey(
        "OrderItem", on_delete=models.CASCADE, null=True, blank=True
    )
    opt = models.ForeignKey("Options", on_delete=models.CASCADE)
    level = models.IntegerField()
