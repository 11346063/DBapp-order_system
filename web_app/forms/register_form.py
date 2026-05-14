from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from web_app.models import Identity, User


class RegisterForm(forms.ModelForm):
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

    class Meta:
        model = User
        fields = ["name", "account", "email", "phone_number", "address"]
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
        normalized = phone_number.replace(" ", "").replace("-", "")
        if (
            normalized
            and not (
                normalized.startswith("09")
                and len(normalized) == 10
                and normalized.isdigit()
            )
            and not (
                normalized.startswith("+8869")
                and len(normalized) == 13
                and normalized[1:].isdigit()
            )
        ):
            raise ValidationError(
                _("請輸入有效的手機號碼，例如 0912345678 或 +886912345678")
            )
        return normalized

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get("password")
        pw2 = cleaned_data.get("password_confirm")
        if pw and pw2 and pw != pw2:
            self.add_error("password_confirm", _("兩次密碼不一致"))
        return cleaned_data


class AdminAccountCreateForm(RegisterForm):
    identity = forms.ChoiceField(
        label=_("帳號權限 *"),
        choices=[
            (Identity.CUSTOMER, _("顧客")),
            (Identity.EMPLOYEE, _("員工")),
            (Identity.ADMIN, _("管理者")),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta(RegisterForm.Meta):
        fields = RegisterForm.Meta.fields + ["identity"]
