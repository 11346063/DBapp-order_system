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

    def test_admin_navigation_hides_customer_history_but_keeps_cart(self):
        self.client.login(username="admin_nav", password="pass")

        response = self.client.get(reverse("web_app:home"))

        self.assertNotContains(response, f'href="{reverse("web_app:order_history")}"')
        self.assertContains(response, f'href="{reverse("web_app:cart")}"')
        self.assertContains(response, f'href="{reverse("web_app:assisted_ordering")}"')
        self.assertContains(response, f'href="{reverse("web_app:staff_orders")}"')
        self.assertContains(response, f'href="{reverse("web_app:account_management")}"')
        self.assertContains(response, f'href="{reverse("web_app:logout")}"')

    def test_mobile_cart_summary_is_hidden_when_cart_is_empty(self):
        self.client.login(username="customer_nav", password="pass")

        response = self.client.get(reverse("web_app:home"))

        self.assertContains(response, 'id="mobileCartSummary"')
        self.assertContains(response, "mobile-cart-summary d-md-none d-none")

    def test_mobile_cart_summary_shows_cart_count(self):
        self.client.login(username="customer_nav", password="pass")
        session = self.client.session
        session["cart"] = [
            {"name": "香脆炸雞", "quantity": 2, "subtotal": 160},
            {"name": "薯條", "quantity": 1, "subtotal": 50},
        ]
        session.save()

        response = self.client.get(reverse("web_app:home"))

        self.assertContains(response, 'id="mobileCartSummary"')
        self.assertContains(response, "購物車")
        self.assertContains(response, 'id="mobileCartSummaryCount">3</span>')

    def test_payment_page_hides_mobile_cart_summary(self):
        self.client.login(username="customer_nav", password="pass")
        session = self.client.session
        session["cart"] = [{"name": "香脆炸雞", "quantity": 2, "subtotal": 160}]
        session.save()

        response = self.client.get(reverse("web_app:payment"))

        self.assertNotContains(response, 'id="mobileCartSummary"')

    def test_login_page_hides_mobile_cart_summary(self):
        session = self.client.session
        session["cart"] = [{"name": "香脆炸雞", "quantity": 3, "subtotal": 240}]
        session.save()

        response = self.client.get(reverse("web_app:login"))

        self.assertNotContains(response, 'id="mobileCartSummary"')

    def test_cart_page_hides_mobile_cart_summary(self):
        self.client.login(username="customer_nav", password="pass")
        session = self.client.session
        session["cart"] = [{"name": "香脆炸雞", "quantity": 2, "subtotal": 160}]
        session.save()

        response = self.client.get(reverse("web_app:cart"))

        self.assertNotContains(response, 'id="mobileCartSummary"')

    def test_admin_mobile_cart_summary_shows_cart_count(self):
        self.client.login(username="admin_nav", password="pass")
        session = self.client.session
        session["cart"] = [{"name": "香脆炸雞", "quantity": 2, "subtotal": 160}]
        session.save()

        response = self.client.get(reverse("web_app:home"))

        self.assertContains(response, 'id="mobileCartSummary"')
        self.assertContains(response, 'id="mobileCartSummaryCount">2</span>')


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
