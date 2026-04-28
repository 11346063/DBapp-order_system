from django.test import Client, TestCase
from django.urls import reverse

from web_app.models import User


class RegistrationValidationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("web_app:register")

    def valid_payload(self, **overrides):
        payload = {
            "name": "新顧客",
            "account": "new_customer",
            "email": "customer@example.com",
            "phone_number": "0912345678",
            "address": "",
            "password": "pass1234",
            "password_confirm": "pass1234",
        }
        payload.update(overrides)
        return payload

    def test_register_rejects_invalid_email(self):
        response = self.client.post(
            self.url,
            self.valid_payload(email="not-an-email"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "請輸入有效的 Email 格式")
        self.assertFalse(User.objects.filter(account="new_customer").exists())

    def test_register_rejects_invalid_phone_number(self):
        response = self.client.post(
            self.url,
            self.valid_payload(phone_number="12345"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "請輸入有效的手機號碼")
        self.assertFalse(User.objects.filter(account="new_customer").exists())

    def test_register_accepts_formatted_taiwan_mobile_number(self):
        response = self.client.post(
            self.url,
            self.valid_payload(phone_number="0912-345-678"),
        )

        self.assertEqual(response.status_code, 302)
        created = User.objects.get(account="new_customer")
        self.assertEqual(created.phone_number, "0912345678")
