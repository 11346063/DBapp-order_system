from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm

from web_app.models import User


class AccountPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "請輸入註冊時使用的 Email",
                "autocomplete": "email",
            }
        ),
    )

    def get_users(self, email):
        matching_users = User.objects.filter(email__iexact=email, status=True)
        for user in matching_users:
            if user.has_usable_password():
                yield user


class AccountSetPasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields["new_password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "請輸入新密碼",
                "autocomplete": "new-password",
            }
        )
        self.fields["new_password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "再次輸入新密碼",
                "autocomplete": "new-password",
            }
        )
