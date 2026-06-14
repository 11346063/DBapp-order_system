from datetime import time

from django.db import models


class StoreSettings(models.Model):
    extra_ingredient_cost = models.PositiveIntegerField(default=10)
    option_name_spicy = models.CharField(max_length=20, default="辣度")
    option_name_garlic = models.CharField(max_length=20, default="加蒜")
    option_name_basil = models.CharField(max_length=20, default="九層塔")
    option_name_cut = models.CharField(max_length=20, default="切")
    business_hours_enabled = models.BooleanField(default=False)
    open_time = models.TimeField(default=time(10, 0))
    close_time = models.TimeField(default=time(21, 0))

    class Meta:
        verbose_name = "系統設定"
