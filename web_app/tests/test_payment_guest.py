from django.test import TestCase, Client
from django.urls import reverse
from web_app.models import User, Identity, Type, Menu, Order


class GuestCheckoutTest(TestCase):
    def setUp(self):
        self.client = Client()
        menu_type = Type.objects.create(type_name='炸雞')
        self.menu = Menu.objects.create(
            type=menu_type,
            name='香脆炸雞',
            price=80,
            status=True,
        )
        self.customer = User.objects.create_user(
            account='customer1', password='pass', name='顧客', identity=Identity.CUSTOMER
        )

    def _set_cart(self):
        session = self.client.session
        session['cart'] = [
            {'menu_id': self.menu.pk, 'name': '香脆炸雞', 'price': 80,
             'quantity': 1, 'subtotal': 80, 'options': []}
        ]
        session.save()

    # --- payment_view ---

    def test_guest_can_access_payment_page(self):
        """未登入訪客可以進入付款頁，不應被重導至登入"""
        self._set_cart()
        response = self.client.get(reverse('web_app:payment'))
        self.assertEqual(response.status_code, 200)

    def test_payment_page_shows_login_prompt_for_guest(self):
        """付款頁對未登入訪客顯示登入詢問提示"""
        self._set_cart()
        response = self.client.get(reverse('web_app:payment'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'guest-login-prompt')

    def test_payment_page_no_login_prompt_for_logged_in_user(self):
        """已登入顧客的付款頁不顯示登入詢問提示"""
        self.client.login(username='customer1', password='pass')
        self._set_cart()
        response = self.client.get(reverse('web_app:payment'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'guest-login-prompt')

    def test_guest_payment_empty_cart_redirects_home(self):
        """訪客購物車為空時，付款頁應導向首頁"""
        response = self.client.get(reverse('web_app:payment'))
        self.assertRedirects(response, reverse('web_app:home'))

    # --- order_submit ---

    def test_guest_can_submit_order(self):
        """未登入訪客可以送出訂單"""
        self._set_cart()
        response = self.client.post(reverse('web_app:order_submit'))
        self.assertRedirects(response, reverse('web_app:home'))

    def test_guest_order_has_null_user(self):
        """訪客送出的訂單 user 欄位為 None"""
        self._set_cart()
        self.client.post(reverse('web_app:order_submit'))
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertIsNone(order.user)

    def test_guest_order_creates_order_item(self):
        """訪客送出的訂單包含正確的 OrderItem"""
        self._set_cart()
        self.client.post(reverse('web_app:order_submit'))
        from web_app.models import OrderItem
        self.assertEqual(OrderItem.objects.count(), 1)
        item = OrderItem.objects.first()
        self.assertEqual(item.amount, 1)
        self.assertEqual(item.total_price, 80)

    def test_guest_order_clears_cart(self):
        """訪客送出訂單後購物車應清空"""
        self._set_cart()
        self.client.post(reverse('web_app:order_submit'))
        cart = self.client.session.get('cart', [])
        self.assertEqual(cart, [])

    def test_logged_in_customer_order_still_has_user(self):
        """已登入顧客送出訂單後，user 欄位正確儲存"""
        self.client.login(username='customer1', password='pass')
        self._set_cart()
        self.client.post(reverse('web_app:order_submit'))
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.user, self.customer)
