from django.db import models

class Order(models.Model):
    sno = models.IntegerField()
    user = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True)
    create_time = models.DateTimeField()
    status = models.IntegerField()
    price_total = models.IntegerField()
    remark = models.CharField(max_length=200, blank=True, default="")