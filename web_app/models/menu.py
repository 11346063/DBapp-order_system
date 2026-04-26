from django.db import models


class Menu(models.Model):
    type = models.ForeignKey("Type", on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)
    price = models.IntegerField()
    info = models.CharField(max_length=100, blank=True, null=True)
    remark = models.CharField(max_length=100, blank=True, null=True)
    file_path = models.ImageField(upload_to="image/", blank=True, null=True)
    status = models.BooleanField(default=True)
