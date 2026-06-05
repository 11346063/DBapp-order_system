from django.test import Client, TestCase
from django.urls import reverse

from web_app.forms.login_form import LoginForm
from web_app.models import User


class RegistrationValidationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("web_app:register")

    def valid_payload(self, **overrides):
        payload = {
            "phone_number": "0912345678",
            "password": "pass1234",
            "password_confirm": "pass1234",
        }
        payload.update(overrides)
        return payload

    def test_register_form_uses_phone_number_as_account(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "手機號碼")
        self.assertContains(response, 'name="phone_number"')
        self.assertNotContains(response, 'name="account"')

    def test_register_rejects_invalid_phone_number(self):
        response = self.client.post(
            self.url,
            self.valid_payload(phone_number="12345"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "請輸入有效的手機號碼")
        self.assertFalse(User.objects.exists())

    def test_register_rejects_duplicate_phone_number(self):
        User.objects.create_user(
            account="0912345678",
            password="pass",
            name="既有顧客",
            phone_number="0912345678",
        )

        response = self.client.post(self.url, self.valid_payload())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "此手機號碼已註冊")
        self.assertEqual(User.objects.filter(account="0912345678").count(), 1)

    def test_register_accepts_formatted_taiwan_mobile_number(self):
        response = self.client.post(
            self.url,
            self.valid_payload(phone_number="0912-345-678"),
        )

        self.assertEqual(response.status_code, 302)
        created = User.objects.get(account="0912345678")
        self.assertEqual(created.phone_number, "0912345678")
        self.assertEqual(created.name, "顧客")
        self.assertTrue(created.check_password("pass1234"))

    def test_register_normalizes_international_taiwan_mobile_number(self):
        response = self.client.post(
            self.url,
            self.valid_payload(phone_number="+886912345678"),
        )

        self.assertEqual(response.status_code, 302)
        created = User.objects.get(account="0912345678")
        self.assertEqual(created.phone_number, "0912345678")


class PhoneLoginFormLabelTest(TestCase):
    def test_login_form_uses_phone_number_wording(self):
        form = LoginForm()

        self.assertEqual(form.fields["account"].label, "手機號碼")
        self.assertEqual(
            form.fields["account"].widget.attrs["placeholder"],
            "請輸入手機號碼",
        )


class LoginFormCleanAccountTest(TestCase):
    def _make_form(self, account):
        return LoginForm(
            data={
                "account": account,
                "password": "pass",
                "captcha_0": "x",
                "captcha_1": "x",
            },
        )

    def test_valid_phone_normalised(self):
        from web_app.forms.login_form import LoginForm as LF

        class _Stub(LF):
            def __init__(self, account_val):
                self.cleaned_data = {"account": account_val}

        stub = _Stub("0912-345-678")
        result = stub.clean_account()
        self.assertEqual(result, "0912345678")

    def test_invalid_phone_raises_validation_error(self):
        from web_app.forms.login_form import LoginForm as LF
        import django.forms as df

        class _Stub(LF):
            def __init__(self, account_val):
                self.cleaned_data = {"account": account_val}

        stub = _Stub("not-a-phone")
        with self.assertRaises(df.ValidationError) as ctx:
            stub.clean_account()
        self.assertIn("台灣手機號碼", str(ctx.exception))
