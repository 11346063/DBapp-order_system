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
        verbose_name = "菜單選項關聯"
        verbose_name_plural = "菜單選項關聯"

    def __str__(self):
        return f"{self.menu} - {self.opt}"
