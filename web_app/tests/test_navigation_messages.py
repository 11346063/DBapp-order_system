from django.test import Client, TestCase
from django.urls import reverse

from web_app.models import Identity, Menu, Type, User


class NavigationVisibilityTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.type = Type.objects.create(type_name="炸雞")
        Menu.objects.create(type=self.type, name="香脆炸雞", price=80, status=True)
        self.customer = User.objects.create_user(
            account="customer_nav",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
        )
        self.admin = User.objects.create_user(
            account="admin_nav",
            password="pass",
            name="管理員",
            identity=Identity.ADMIN,
        )

    def test_customer_keeps_history_and_cart_navigation(self):
        self.client.login(username="customer_nav", password="pass")

        response = self.client.get(reverse("web_app:home"))

        self.assertContains(response, f'href="{reverse("web_app:order_history")}"')
        self.assertContains(response, f'href="{reverse("web_app:cart")}"')

    def test_admin_navigation_hides_customer_history_and_cart(self):
        self.client.login(username="admin_nav", password="pass")

        response = self.client.get(reverse("web_app:home"))

        self.assertNotContains(response, f'href="{reverse("web_app:order_history")}"')
        self.assertNotContains(response, f'href="{reverse("web_app:cart")}"')
        self.assertContains(response, f'href="{reverse("web_app:staff_orders")}"')
        self.assertContains(response, f'href="{reverse("web_app:logout")}"')


class SuccessMessageAutoDismissTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            account="message_user",
            password="pass",
            name="訊息測試",
            identity=Identity.CUSTOMER,
        )

    def test_logout_success_message_is_marked_for_auto_dismiss(self):
        self.client.login(username="message_user", password="pass")

        response = self.client.get(reverse("web_app:logout"), follow=True)

        self.assertContains(response, "已成功登出")
        self.assertContains(response, 'data-auto-dismiss="success"')
