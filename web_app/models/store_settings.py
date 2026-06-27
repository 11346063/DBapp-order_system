from datetime import time

from django.db import models


class StoreSettings(models.Model):
    business_hours_enabled = models.BooleanField(default=False)
    open_time = models.TimeField(default=time(10, 0))
    close_time = models.TimeField(default=time(21, 0))

    class Meta:
        verbose_name = "系統設定"
