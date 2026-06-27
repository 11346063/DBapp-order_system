from django.db import models


class Options(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.IntegerField()
    is_custom_extra = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "選項"
        verbose_name_plural = "選項"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="options_price_non_negative",
            )
        ]

    def __str__(self):
        return self.name
