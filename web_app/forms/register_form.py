from django import forms
from web_app.models import Identity, User


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label="密碼 *",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "請輸入密碼",
                "autocomplete": "new-password",
            }
        ),
    )
    password_confirm = forms.CharField(
        label="確認密碼 *",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "再次輸入密碼",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["name", "account", "email", "phone_number", "address"]
        labels = {
            "name": "名字 *",
            "account": "帳號 *",
            "email": "Email",
            "phone_number": "電話號碼",
            "address": "地址",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "請輸入名字"}
            ),
            "account": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "請輸入帳號"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "選填"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "選填"}
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "選填"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get("password")
        pw2 = cleaned_data.get("password_confirm")
        if pw and pw2 and pw != pw2:
            self.add_error("password_confirm", "兩次密碼不一致")
        return cleaned_data


class AdminAccountCreateForm(RegisterForm):
    identity = forms.ChoiceField(
        label="帳號權限 *",
        choices=[
            (Identity.CUSTOMER, "顧客"),
            (Identity.EMPLOYEE, "員工"),
            (Identity.ADMIN, "管理者"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta(RegisterForm.Meta):
        fields = RegisterForm.Meta.fields + ["identity"]
