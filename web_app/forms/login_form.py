from django import forms
from django.utils.translation import gettext_lazy as _
from captcha.fields import CaptchaField

from web_app.utils.phone import PhoneValidationError, normalize_tw_mobile


class LoginForm(forms.Form):
    account = forms.CharField(
        max_length=20,
        label=_("手機號碼"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("請輸入手機號碼"),
                "autocomplete": "username",
                "inputmode": "tel",
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

    def clean_account(self):
        account = self.cleaned_data["account"].strip()
        try:
            return normalize_tw_mobile(account)
        except PhoneValidationError:
            return account
