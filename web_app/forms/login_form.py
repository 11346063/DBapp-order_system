from django import forms
from django.utils.translation import gettext_lazy as _
from captcha.fields import CaptchaField


class LoginForm(forms.Form):
    account = forms.CharField(
        max_length=20,
        label=_("帳號"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("請輸入帳號"),
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label=_("密碼"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("請輸入密碼"),
                "autocomplete": "current-password",
            }
        ),
    )
    captcha = CaptchaField(label=_("驗證碼"))
