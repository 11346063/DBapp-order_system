from django import forms


class LoginForm(forms.Form):
    account = forms.CharField(
        max_length=20,
        label='帳號',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '請輸入帳號',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        label='密碼',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '請輸入密碼',
            'autocomplete': 'current-password',
        })
    )
