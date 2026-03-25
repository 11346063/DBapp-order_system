from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

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
        # 建立超級管理員時，強制設定以下權限為 True
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('identity', 'A') 

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser 必須設定 is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser 必須設定 is_superuser=True.')

        return self.create_user(account, password, **extra_fields)

# 這裡要多繼承 PermissionsMixin
class User(AbstractBaseUser, PermissionsMixin):
    account = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    identity = models.CharField(max_length=1)
    
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    
    # --- 新增以下三個 Django Admin 必備欄位 ---
    is_staff = models.BooleanField(default=False)    # 決定能否登入管理後台
    is_superuser = models.BooleanField(default=False) # 決定是否擁有所有權限
    is_active = models.BooleanField(default=True)     # 帳號是否有效（被停權可設為 False）
    # ---------------------------------------

    status = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'account'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.account