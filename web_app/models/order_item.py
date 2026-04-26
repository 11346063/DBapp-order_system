from django.db import models


class OrderItem(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE)
    menu = models.ForeignKey("Menu", on_delete=models.CASCADE)
    amount = models.IntegerField()
    total_price = models.IntegerField()
