import json

from django.test import TestCase, Client
from django.urls import reverse

from web_app.models import User, Identity, Type, Menu, Order
from web_app.tests.test_helpers import seed_system_options


class GuestCheckoutTest(TestCase):
    def setUp(self):
        seed_system_options()
        self.client = Client()
        menu_type = Type.objects.create(type_name="炸雞")
        self.menu = Menu.objects.create(
            type=menu_type,
            name="香脆炸雞",
            price=80,
            status=True,
        )
        self.customer = User.objects.create_user(
            account="customer1",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
            phone_number="0912345678",
        )
        self.employee = User.objects.create_user(
            account="employee1",
            password="pass",
            name="員工",
            identity=Identity.EMPLOYEE,
        )

    def _cart_json(self):
        return json.dumps(
            [
                {
                    "menu_id": self.menu.pk,
                    "name": self.menu.name,
                    "base_price": self.menu.price,
                    "options": [],
                    "options_price": 0,
                    "unit_price": self.menu.price,
                    "quantity": 1,
                    "subtotal": self.menu.price,
                }
            ]
        )

    # --- payment_view ---

    def test_guest_can_access_payment_page(self):
        """未登入訪客可以進入付款頁，不應被重導至登入"""
        response = self.client.get(reverse("web_app:payment"))
        self.assertEqual(response.status_code, 200)

    def test_payment_page_shows_login_prompt_for_guest(self):
        """付款頁對未登入訪客顯示登入詢問提示"""
        response = self.client.get(reverse("web_app:payment"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "guest-login-prompt")
        self.assertContains(response, "payment-summary-col")
        self.assertContains(response, "payment-submit-card")
        self.assertContains(response, "css/payment.css")
        self.assertContains(response, 'id="cartPriceChangeModal"')
        self.assertContains(response, 'id="acceptPaymentPriceChanges"')
        self.assertContains(response, "js/payment.js")
        self.assertContains(response, "?v=8")
        self.assertContains(response, "聯絡電話")
        self.assertContains(response, 'name="customer_phone"')

    def test_payment_page_no_login_prompt_for_logged_in_user(self):
        """已登入顧客的付款頁不顯示登入詢問提示"""
        self.client.login(username="customer1", password="pass")
        response = self.client.get(reverse("web_app:payment"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "guest-login-prompt")
        self.assertContains(response, 'value="0912345678"')

    def test_employee_can_access_payment_page_with_phone_field(self):
        """員工代客點餐可以進入付款頁，且必須看到客人電話欄位"""
        self.client.login(username="employee1", password="pass")
        response = self.client.get(reverse("web_app:payment"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "電話代客點餐")
        self.assertContains(response, 'name="customer_phone"')
        self.assertContains(response, "客人電話")

    # --- order_submit ---

    def test_guest_can_submit_order(self):
        """未登入訪客可以送出訂單，結帳後跳至等待確認頁"""
        response = self.client.post(
            reverse("web_app:order_submit"),
            data={
                "customer_phone": "0912345678",
                "cart_json": self._cart_json(),
            },
        )
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertRedirects(
            response, reverse("web_app:order_waiting", kwargs={"pk": order.pk})
        )

    def test_guest_order_requires_customer_phone(self):
        """訪客送單必須填寫聯絡電話"""
        response = self.client.post(
            reverse("web_app:order_submit"),
            data={"cart_json": self._cart_json()},
        )
        self.assertRedirects(response, reverse("web_app:payment"))
        self.assertEqual(Order.objects.count(), 0)

    def test_guest_order_has_null_user(self):
        """訪客送出的訂單 user 欄位為 None"""
        self.client.post(
            reverse("web_app:order_submit"),
            data={
                "customer_phone": "0912345678",
                "cart_json": self._cart_json(),
            },
        )
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertIsNone(order.user)
        self.assertEqual(order.customer_phone, "0912345678")

    def test_guest_order_creates_order_item(self):
        """訪客送出的訂單包含正確的 OrderItem"""
        self.client.post(
            reverse("web_app:order_submit"),
            data={
                "customer_phone": "0912345678",
                "cart_json": self._cart_json(),
            },
        )
        from web_app.models import OrderItem

        self.assertEqual(OrderItem.objects.count(), 1)
        item = OrderItem.objects.first()
        self.assertEqual(item.amount, 1)
        self.assertEqual(item.total_price, 80)

    def test_logged_in_customer_order_still_has_user(self):
        """已登入顧客送出訂單後，user 欄位正確儲存"""
        self.client.login(username="customer1", password="pass")
        self.client.post(
            reverse("web_app:order_submit"),
            data={"cart_json": self._cart_json()},
        )
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.user, self.customer)
        self.assertEqual(order.customer_phone, "0912345678")

    def test_employee_order_requires_customer_phone(self):
        """員工代客點餐未填電話時不建立訂單"""
        self.client.login(username="employee1", password="pass")
        response = self.client.post(
            reverse("web_app:order_submit"),
            data={"cart_json": self._cart_json()},
        )
        self.assertRedirects(response, reverse("web_app:payment"))
        self.assertEqual(Order.objects.count(), 0)

    def test_employee_order_saves_customer_phone(self):
        """員工代客點餐會把客人電話註記在訂單上"""
        self.client.login(username="employee1", password="pass")
        self.client.post(
            reverse("web_app:order_submit"),
            data={
                "customer_phone": "0912345678",
                "cart_json": self._cart_json(),
            },
        )
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.user, self.employee)
        self.assertEqual(order.customer_phone, "0912345678")

    def test_checkout_normalizes_international_taiwan_mobile_number(self):
        """結帳電話支援台灣國碼格式並正規化保存"""
        self.client.post(
            reverse("web_app:order_submit"),
            data={
                "customer_phone": "+886912345678",
                "cart_json": self._cart_json(),
            },
        )
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.customer_phone, "0912345678")
