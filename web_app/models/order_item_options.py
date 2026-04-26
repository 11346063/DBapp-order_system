from django.db import models


class OrderItemOptions(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE)
    opt = models.ForeignKey("Options", on_delete=models.CASCADE)
    level = models.IntegerField()

    class Meta:
        unique_together = ("order", "opt")
