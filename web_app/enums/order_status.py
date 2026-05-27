from django.db import models


class OrderStatus(models.IntegerChoices):
    SUBMITTED = 0, "等待接單"
    ACCEPTED = 1, "備餐中"
    READY = 2, "可取餐"
    COMPLETED = 3, "已完成"
    CANCELLED = 4, "已取消"
