from django.db import models


class Identity(models.TextChoices):
    ADMIN = "A", "管理員"
    EMPLOYEE = "E", "員工"
    CUSTOMER = "C", "顧客"
    GUEST = "G", "訪客"
