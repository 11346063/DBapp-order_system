from django.test import Client, TestCase
from django.urls import reverse

from web_app.models import Identity, User


class AccountManagementTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            account="account_admin",
            password="pass",
            name="管理者",
            identity=Identity.ADMIN,
        )
        self.employee = User.objects.create_user(
            account="account_employee",
            password="pass",
            name="員工",
            identity=Identity.EMPLOYEE,
        )
        self.customer = User.objects.create_user(
            account="account_customer",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
        )
        self.url = reverse("web_app:account_management")

    def test_admin_can_view_all_accounts(self):
        self.client.login(username="account_admin", password="pass")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "管理者帳號管理")
        self.assertContains(response, "account_admin")
        self.assertContains(response, "account_employee")
        self.assertContains(response, "account_customer")
        self.assertContains(response, "建立帳號")

    def test_employee_cannot_view_account_management(self):
        self.client.login(username="account_employee", password="pass")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("web_app:staff_orders"))

    def test_admin_can_filter_employee_accounts(self):
        self.client.login(username="account_admin", password="pass")

        response = self.client.get(self.url, {"identity": Identity.EMPLOYEE})

        self.assertContains(response, "account_employee")
        self.assertNotContains(response, "account_customer")

    def test_admin_can_create_employee_account(self):
        self.client.login(username="account_admin", password="pass")

        response = self.client.post(
            self.url,
            {
                "name": "新員工",
                "account": "new_employee",
                "email": "employee@example.com",
                "phone_number": "",
                "address": "",
                "identity": Identity.EMPLOYEE,
                "password": "pass1234",
                "password_confirm": "pass1234",
            },
        )

        self.assertEqual(response.status_code, 302)
        created = User.objects.get(account="new_employee")
        self.assertEqual(created.identity, Identity.EMPLOYEE)
        self.assertTrue(created.check_password("pass1234"))
