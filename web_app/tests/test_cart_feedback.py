from django.test import Client, TestCase
from django.urls import reverse

from web_app.models import Identity, Menu, Type, User


class CartFeedbackTemplateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.type = Type.objects.create(type_name="炸雞")
        Menu.objects.create(type=self.type, name="香脆炸雞", price=80, status=True)
        self.customer = User.objects.create_user(
            account="cart_feedback_user",
            password="pass",
            name="回流測試",
            identity=Identity.CUSTOMER,
        )

    def test_home_includes_cart_feedback_actions(self):
        self.client.login(username="cart_feedback_user", password="pass")

        response = self.client.get(reverse("web_app:home"))

        self.assertContains(response, 'id="cartFeedback"')
        self.assertContains(response, 'class="cart-feedback d-none"')
        self.assertContains(response, 'data-cart-action="continue"')
        self.assertContains(response, 'data-bs-dismiss="modal"')
        self.assertContains(response, 'data-bs-dismiss="offcanvas"')
        self.assertContains(response, 'data-cart-action="dismiss-feedback"')
        self.assertContains(response, "繼續點餐")
        self.assertContains(response, "查看購物車")
        self.assertContains(response, f'href="{reverse("web_app:cart")}"')

    def test_home_keeps_cart_feedback_visible_when_cart_has_items(self):
        self.client.login(username="cart_feedback_user", password="pass")
        session = self.client.session
        session["cart"] = [{"name": "香脆炸雞", "quantity": 2, "subtotal": 160}]
        session.save()

        response = self.client.get(reverse("web_app:home"))

        self.assertContains(response, 'id="cartFeedback"')
        self.assertContains(response, "購物車目前有 2 件商品")
        self.assertContains(response, 'id="cartFeedback" class="cart-feedback "')
        self.assertNotContains(response, 'class="cart-feedback d-none"')


class CartPageNavigationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.type = Type.objects.create(type_name="炸雞")
        self.menu = Menu.objects.create(
            type=self.type,
            name="香脆炸雞",
            price=80,
            status=True,
        )

    def _set_cart(self):
        session = self.client.session
        session["cart"] = [
            {
                "menu_id": self.menu.pk,
                "name": "香脆炸雞",
                "base_price": 80,
                "options": [],
                "options_price": 0,
                "unit_price": 80,
                "quantity": 1,
                "subtotal": 80,
            }
        ]
        session.save()

    def test_cart_page_has_return_to_ordering_button(self):
        self._set_cart()

        response = self.client.get(reverse("web_app:cart"))

        self.assertContains(response, "返回點餐")
        self.assertContains(response, f'href="{reverse("web_app:home")}"')
