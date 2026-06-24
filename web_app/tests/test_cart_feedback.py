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

    def test_employee_home_keeps_ordering_actions_separate(self):
        """員工菜單管理頁不混入代客點餐操作"""
        self.client.login(username="cart_emp", password="pass")

        response = self.client.get(reverse("web_app:home"))

        self.assertTrue(response.context["is_staff"])
        self.assertNotContains(response, 'class="customer-actions"')
        self.assertNotContains(response, "加入購物車")
        self.assertNotContains(response, 'id="cartFeedback"')

    def test_employee_assisted_ordering_includes_customer_ordering_actions(self):
        """員工代客點餐頁使用單頁雙欄 UI：左側菜單卡片、右側訂單草稿與送出按鈕"""
        self.client.login(username="cart_emp", password="pass")

        response = self.client.get(reverse("web_app:assisted_ordering"))

        self.assertIn("menus", response.context)
        self.assertIn("custom_options", response.context)
        self.assertIn("extra_ingredient_cost", response.context)
        self.assertContains(response, "assisted-menu-card")
        self.assertContains(response, "訂單清單")
        self.assertContains(response, "送出訂單")
        self.assertContains(response, "客人電話")
        self.assertContains(response, "加入購物車")
        self.assertNotContains(response, "data-assisted-delta")
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

    def test_cart_page_has_return_to_ordering_button(self):
        response = self.client.get(reverse("web_app:cart"))

        self.assertContains(response, "返回點餐")
        self.assertContains(response, f'href="{reverse("web_app:home")}"')
        self.assertContains(response, "css/cart.css")
        self.assertContains(response, "?v=3")

    def test_employee_can_access_cart_page(self):
        employee = User.objects.create_user(
            account="cart_page_emp",
            password="pass",
            name="代客員工",
            identity=Identity.EMPLOYEE,
        )
        self.client.login(username=employee.account, password="pass")

        response = self.client.get(reverse("web_app:cart"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "購物車")
        self.assertContains(response, f'href="{reverse("web_app:assisted_ordering")}"')
