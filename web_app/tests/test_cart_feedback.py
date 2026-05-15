from django.test import Client, TestCase
from django.urls import reverse
import json

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
        self.employee = User.objects.create_user(
            account="cart_emp",
            password="pass",
            name="代客員工",
            identity=Identity.EMPLOYEE,
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

    def test_guest_home_sets_csrf_cookie_for_cart_ajax(self):
        """訪客首頁需要設定 CSRF cookie，加入購物車 AJAX 才不會被 403 擋下"""
        response = self.client.get(reverse("web_app:home"))

        self.assertIn("csrftoken", response.cookies)

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

    def test_employee_home_keeps_ordering_actions_separate(self):
        """員工菜單管理頁不混入代客點餐操作"""
        self.client.login(username="cart_emp", password="pass")

        response = self.client.get(reverse("web_app:home"))

        self.assertTrue(response.context["is_staff"])
        self.assertNotContains(response, 'class="customer-actions"')
        self.assertNotContains(response, "加入購物車")
        self.assertNotContains(response, 'id="cartFeedback"')

    def test_employee_assisted_ordering_includes_customer_ordering_actions(self):
        """員工代客點餐頁使用精簡數量控制，不顯示圖片與詳情彈窗操作"""
        self.client.login(username="cart_emp", password="pass")

        response = self.client.get(reverse("web_app:assisted_ordering"))

        self.assertFalse(response.context["is_staff"])
        self.assertTrue(response.context["show_customer_ordering"])
        self.assertTrue(response.context["is_assisted_ordering"])
        self.assertContains(response, "assisted-item-card")
        self.assertContains(response, 'data-assisted-delta="-1"')
        self.assertContains(response, 'data-assisted-delta="1"')
        self.assertContains(response, 'id="cartFeedback"')
        self.assertContains(response, f'href="{reverse("web_app:cart")}"')
        self.assertNotContains(response, "card-img-top-placeholder")
        self.assertNotContains(response, "加入購物車")
        self.assertNotContains(response, "編輯品項")


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
        self.assertContains(response, "css/cart.css")
        self.assertContains(response, "?v=2")

    def test_employee_can_access_cart_page(self):
        employee = User.objects.create_user(
            account="cart_page_emp",
            password="pass",
            name="代客員工",
            identity=Identity.EMPLOYEE,
        )
        self.client.login(username=employee.account, password="pass")
        self._set_cart()

        response = self.client.get(reverse("web_app:cart"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "購物車")
        self.assertContains(response, f'href="{reverse("web_app:assisted_ordering")}"')

    def test_employee_can_add_to_cart(self):
        employee = User.objects.create_user(
            account="cart_add_emp",
            password="pass",
            name="代客員工",
            identity=Identity.EMPLOYEE,
        )
        self.client.login(username=employee.account, password="pass")

        response = self.client.post(
            reverse("web_app:cart_add_api"),
            data=json.dumps(
                {
                    "menu_id": self.menu.pk,
                    "name": self.menu.name,
                    "price": self.menu.price,
                    "quantity": 1,
                    "options": [],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    def test_employee_can_adjust_assisted_cart_quantity(self):
        employee = User.objects.create_user(
            account="cart_adjust_emp",
            password="pass",
            name="代客員工",
            identity=Identity.EMPLOYEE,
        )
        self.client.login(username=employee.account, password="pass")

        add_response = self.client.post(
            reverse("web_app:cart_adjust_api"),
            data=json.dumps(
                {
                    "menu_id": self.menu.pk,
                    "name": self.menu.name,
                    "price": self.menu.price,
                    "delta": 1,
                }
            ),
            content_type="application/json",
        )
        remove_response = self.client.post(
            reverse("web_app:cart_adjust_api"),
            data=json.dumps(
                {
                    "menu_id": self.menu.pk,
                    "name": self.menu.name,
                    "price": self.menu.price,
                    "delta": -1,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(add_response.status_code, 200)
        self.assertEqual(add_response.json()["data"]["item_quantity"], 1)
        self.assertEqual(add_response.json()["data"]["cart_count"], 1)
        self.assertEqual(remove_response.status_code, 200)
        self.assertEqual(remove_response.json()["data"]["item_quantity"], 0)
        self.assertEqual(remove_response.json()["data"]["cart_count"], 0)
