from django.db import models


class Options(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.IntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name="options_price_non_negative",
            )
        ]
