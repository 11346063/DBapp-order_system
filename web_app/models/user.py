from django.db import models

class User(models.Model):
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    identity = models.CharField(max_length=1)
    create_time = models.DateTimeField()
    update_time = models.DateTimeField()
    status = models.BooleanField()
    account = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=100)