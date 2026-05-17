from django.db import models


class OptGroup(models.Model):
    menu = models.ForeignKey(
        "Menu", on_delete=models.CASCADE, related_name="opt_groups"
    )
    opt = models.ForeignKey(
        "Options", on_delete=models.CASCADE, related_name="opt_groups"
    )

    class Meta:
        unique_together = ("menu", "opt")
