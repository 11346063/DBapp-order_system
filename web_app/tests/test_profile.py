from django.test import Client, TestCase
from django.urls import reverse

from web_app.models import Identity, User


class ProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = User.objects.create_user(
            account="0912345678",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
            phone_number="0912345678",
        )
        self.employee = User.objects.create_user(
            account="profile_employee",
            password="pass",
            name="員工",
            identity=Identity.EMPLOYEE,
        )
        self.url = reverse("web_app:profile")

    def test_guest_redirects_to_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("web_app:login"), response.url)

    def test_customer_can_view_profile_form(self):
        self.client.login(username="0912345678", password="pass")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "個人資料")
        self.assertContains(response, "登入手機號碼")
        self.assertContains(response, 'value="0912345678"')
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="address"')
        self.assertNotContains(response, 'name="phone_number"')

    def test_customer_can_update_profile(self):
        self.client.login(username="0912345678", password="pass")

        response = self.client.post(
            self.url,
            {
                "name": "林小龍",
                "email": "dragon@example.com",
                "address": "台北市中正區",
            },
        )

        self.assertRedirects(response, self.url)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, "林小龍")
        self.assertEqual(self.customer.email, "dragon@example.com")
        self.assertEqual(self.customer.address, "台北市中正區")
        self.assertEqual(self.customer.phone_number, "0912345678")
        self.assertEqual(self.customer.account, "0912345678")

    def test_blank_name_uses_default_customer_name(self):
        self.client.login(username="0912345678", password="pass")

        self.client.post(
            self.url,
            {
                "name": "",
                "email": "",
                "address": "",
            },
        )

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, "顧客")

    def test_employee_redirects_to_staff_orders(self):
        self.client.login(username="profile_employee", password="pass")

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("web_app:staff_orders"))
