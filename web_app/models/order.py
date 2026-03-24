from django.db import models

class Order(models.Model):
    sno = models.IntegerField()
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    create_time = models.DateTimeField()
    status = models.IntegerField()
    price_total = models.IntegerField()