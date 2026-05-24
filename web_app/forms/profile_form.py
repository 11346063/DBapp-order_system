from django import forms
from django.utils.translation import gettext_lazy as _

from web_app.models import User


class ProfileForm(forms.ModelForm):
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

    class Meta:
        model = User
        fields = ["name", "email", "address"]
        labels = {
            "name": _("姓名"),
            "email": "Email",
            "address": _("地址"),
        }
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("請輸入姓名"),
                    "autocomplete": "name",
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("選填"),
                    "autocomplete": "street-address",
                }
            ),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        return name or _("顧客")
