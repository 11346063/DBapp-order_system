from django.db import models


class Options(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.IntegerField()
    is_custom_extra = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="options_price_non_negative",
            )
        ]
