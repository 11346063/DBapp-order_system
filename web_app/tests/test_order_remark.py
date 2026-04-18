from django.test import TestCase, Client
from django.urls import reverse
from web_app.models import Type, Menu, Order


class OrderRemarkTest(TestCase):
    def setUp(self):
        self.client = Client()
        menu_type = Type.objects.create(type_name='炸雞')
        self.menu = Menu.objects.create(
            type=menu_type,
            name='香脆炸雞',
            price=80,
            status=True,
        )

    def _set_cart(self):
        session = self.client.session
        session['cart'] = [
            {'menu_id': self.menu.pk, 'name': '香脆炸雞', 'price': 80,
             'quantity': 1, 'subtotal': 80, 'options': []}
        ]
        session.save()

    def test_remark_saved_when_provided(self):
        """送出訂單時帶備註，Order.remark 應正確存入"""
        self._set_cart()
        self.client.post(reverse('web_app:order_submit'), {'remark': '少辣、不要蔥'})
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.remark, '少辣、不要蔥')

    def test_remark_empty_when_not_provided(self):
        """送出訂單時不帶備註，Order.remark 應為空字串"""
        self._set_cart()
        self.client.post(reverse('web_app:order_submit'))
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(order.remark, '')

    def test_remark_truncated_to_200_chars(self):
        """備註超過 200 字元，後端截斷為 200 字元"""
        self._set_cart()
        long_remark = 'A' * 250
        self.client.post(reverse('web_app:order_submit'), {'remark': long_remark})
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertEqual(len(order.remark), 200)

    def test_guest_can_submit_order_with_remark(self):
        """未登入訪客送出含備註的訂單，應正常成功並存入備註"""
        self._set_cart()
        response = self.client.post(
            reverse('web_app:order_submit'), {'remark': '不要辣椒'}
        )
        self.assertRedirects(response, reverse('web_app:home'))
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertIsNone(order.user)
        self.assertEqual(order.remark, '不要辣椒')
