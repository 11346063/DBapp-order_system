from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from web_app.models import Identity, User
from web_app.utils.phone import PhoneValidationError, normalize_tw_mobile


class RegisterForm(forms.ModelForm):
    phone_number = forms.CharField(
        label=_("手機號碼 *"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("請輸入手機號碼，例如 0912345678"),
                "inputmode": "tel",
                "autocomplete": "tel",
            }
        ),
    )
    password = forms.CharField(
        label=_("密碼 *"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("請輸入密碼"),
                "autocomplete": "new-password",
            }
        ),
    )
    password_confirm = forms.CharField(
        label=_("確認密碼 *"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("再次輸入密碼"),
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["phone_number"]
        labels = {
            "phone_number": _("手機號碼 *"),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number", "")
        try:
            normalized = normalize_tw_mobile(phone_number)
        except PhoneValidationError as exc:
            raise ValidationError(
                _("請輸入有效的手機號碼，例如 0912345678 或 +886912345678")
            ) from exc
        if User.objects.filter(account=normalized).exists():
            raise ValidationError(_("此手機號碼已註冊"))
        return normalized

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get("password")
        pw2 = cleaned_data.get("password_confirm")
        if pw and pw2 and pw != pw2:
            self.add_error("password_confirm", _("兩次密碼不一致"))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        phone_number = self.cleaned_data["phone_number"]
        user.account = phone_number
        user.phone_number = phone_number
        if not user.name:
            user.name = _("顧客")
        if commit:
            user.save()
        return user


class AdminAccountCreateForm(forms.ModelForm):
    email = forms.EmailField(
        label="Email",
        required=False,
        error_messages={"invalid": _("請輸入有效的 Email 格式")},
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": _("選填"),
                "autocomplete": "email",
            }
        ),
    )
    phone_number = forms.CharField(
        label=_("手機號碼"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("選填，例如 0912345678"),
                "inputmode": "tel",
                "autocomplete": "tel",
            }
        ),
    )
    password = forms.CharField(
        label=_("密碼 *"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("請輸入密碼"),
                "autocomplete": "new-password",
            }
        ),
    )
    password_confirm = forms.CharField(
        label=_("確認密碼 *"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("再次輸入密碼"),
                "autocomplete": "new-password",
            }
        ),
    )
    identity = forms.ChoiceField(
        label=_("帳號權限 *"),
        choices=[
            (Identity.CUSTOMER, _("顧客")),
            (Identity.EMPLOYEE, _("員工")),
            (Identity.ADMIN, _("管理者")),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = User
        fields = ["name", "account", "email", "phone_number", "address", "identity"]
        labels = {
            "name": _("名字 *"),
            "account": _("帳號 *"),
            "email": "Email",
            "phone_number": _("手機號碼"),
            "address": _("地址"),
        }
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("請輸入名字")}
            ),
            "account": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("請輸入帳號")}
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("選填")}
            ),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number", "")
        try:
            normalized = normalize_tw_mobile(phone_number)
        except PhoneValidationError as exc:
            raise ValidationError(
                _("請輸入有效的手機號碼，例如 0912345678 或 +886912345678")
            ) from exc
        return normalized

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get("password")
        pw2 = cleaned_data.get("password_confirm")
        if pw and pw2 and pw != pw2:
            self.add_error("password_confirm", _("兩次密碼不一致"))
        return cleaned_data
