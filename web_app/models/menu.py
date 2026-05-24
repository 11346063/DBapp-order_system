from django.db import models


class Menu(models.Model):
    type = models.ForeignKey("Type", on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)
    price = models.IntegerField()
    info = models.CharField(max_length=100, blank=True, null=True)
    remark = models.CharField(max_length=100, blank=True, null=True)
    file_path = models.ImageField(upload_to="image/", blank=True, null=True)
    status = models.BooleanField(default=True)
    options = models.ManyToManyField("Options", through="OptGroup")

    class Meta:
        indexes = [
            # 菜單頁常以 (type, status) 過濾，加速分類+上架狀態的複合查詢
            models.Index(fields=["type", "status"], name="menu_type_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="menu_price_non_negative",
            )
        ]
