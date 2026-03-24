from django.db import models

class Menu(models.Model):
    type = models.ForeignKey('Type', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)
    price = models.IntegerField()
    opt_group_id = models.IntegerField()  # 照你的 SQL 保留
    info = models.CharField(max_length=100, blank=True, null=True)
    remark = models.CharField(max_length=100, blank=True, null=True)