from django.db import models


class OrderItemOptions(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE, null=True, blank=True)
    order_item = models.ForeignKey(
        "OrderItem", on_delete=models.CASCADE, null=True, blank=True
    )
    opt = models.ForeignKey("Options", on_delete=models.CASCADE)
    level = models.IntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(order__isnull=False, order_item__isnull=True)
                    | models.Q(order__isnull=True, order_item__isnull=False)
                ),
                name="orderitemoptions_exactly_one_fk",
            )
        ]
