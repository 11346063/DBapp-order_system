from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, account, password=None, **extra_fields):
        if not account:
            raise ValueError('必須輸入帳號')
        user = self.model(account=account, **extra_fields)
        user.set_password(password)  # 這裡會自動幫你加密 (Pbkdf2_sha256)
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    # 改用繼承， password 欄位 AbstractBaseUser 已經內建並會自動加密
    account = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    identity = models.CharField(max_length=1)
    
    # auto_now_add: 建立時自動產生, auto_now: 每次儲存時自動更新
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    
    status = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'account'  # 指定登入時使用的欄位
    REQUIRED_FIELDS = ['name']  # 建立時必填的欄位

    def __str__(self):
        return self.account