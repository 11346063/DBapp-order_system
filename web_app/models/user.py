from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class Identity(models.TextChoices):
    ADMIN    = 'A', '管理員'
    EMPLOYEE = 'B', '員工'
    CUSTOMER = 'C', '顧客'


class UserManager(BaseUserManager):
    def create_user(self, account, password=None, **extra_fields):
        if not account:
            raise ValueError('必須輸入帳號')

        if 'email' in extra_fields:
            extra_fields['email'] = self.normalize_email(extra_fields['email'])

        user = self.model(account=account, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, account, password=None, **extra_fields):
        extra_fields.setdefault('identity', Identity.ADMIN)
        return self.create_user(account, password, **extra_fields)


class User(AbstractBaseUser):
    account = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    identity = models.CharField(
        max_length=1,
        choices=Identity.choices,
        default=Identity.CUSTOMER,
    )
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'account'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.account

    def has_perm(self, perm, obj=None):
        """管理員擁有所有權限"""
        return self.identity == Identity.ADMIN

    def has_module_perms(self, app_label):
        """管理員擁有所有模組權限"""
        return self.identity == Identity.ADMIN
