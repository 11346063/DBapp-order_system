from django.db import models


class OptGroup(models.Model):
    menu = models.ForeignKey("Menu", on_delete=models.CASCADE)
    opt = models.ForeignKey("Options", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("menu", "opt")
