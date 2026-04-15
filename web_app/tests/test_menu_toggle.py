import json
from django.test import TestCase, Client
from django.urls import reverse
from web_app.models import User, Identity, Type, Menu


class MenuToggleStatusTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.type = Type.objects.create(type_name='炸雞')
        self.active_item = Menu.objects.create(
            type=self.type,
            name='香脆炸雞',
            price=80,
            status=True,
        )
        self.inactive_item = Menu.objects.create(
            type=self.type,
            name='已售完品項',
            price=100,
            status=False,
        )
        self.customer = User.objects.create_user(
            account='customer1', password='pass', name='顧客', identity=Identity.CUSTOMER
        )
        self.employee = User.objects.create_user(
            account='employee1', password='pass', name='員工', identity=Identity.EMPLOYEE
        )
        self.admin = User.objects.create_user(
            account='admin1', password='pass', name='管理員', identity=Identity.ADMIN
        )

    def _toggle_url(self, pk):
        return reverse('web_app:menu_toggle', kwargs={'pk': pk})

    def test_employee_can_toggle_active_to_inactive(self):
        """員工可以將上架商品切換為下架"""
        self.client.login(username='employee1', password='pass')
        response = self.client.post(self._toggle_url(self.active_item.pk))
        self.assertEqual(response.status_code, 200)
        self.active_item.refresh_from_db()
        self.assertFalse(self.active_item.status)

    def test_employee_can_toggle_inactive_to_active(self):
        """員工可以將下架商品切換為上架"""
        self.client.login(username='employee1', password='pass')
        response = self.client.post(self._toggle_url(self.inactive_item.pk))
        self.assertEqual(response.status_code, 200)
        self.inactive_item.refresh_from_db()
        self.assertTrue(self.inactive_item.status)

    def test_admin_can_toggle_status(self):
        """管理員可以切換商品上下架"""
        self.client.login(username='admin1', password='pass')
        response = self.client.post(self._toggle_url(self.active_item.pk))
        self.assertEqual(response.status_code, 200)
        self.active_item.refresh_from_db()
        self.assertFalse(self.active_item.status)

    def test_toggle_returns_json_with_new_status(self):
        """切換後回傳 JSON 包含新的 status"""
        self.client.login(username='employee1', password='pass')
        response = self.client.post(self._toggle_url(self.active_item.pk))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('status', data)
        self.assertFalse(data['status'])

    def test_customer_cannot_toggle_status(self):
        """顧客無法切換商品上下架（403）"""
        self.client.login(username='customer1', password='pass')
        response = self.client.post(self._toggle_url(self.active_item.pk))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_toggle_status(self):
        """未登入使用者無法切換商品上下架（重導向登入頁）"""
        response = self.client.post(self._toggle_url(self.active_item.pk))
        self.assertEqual(response.status_code, 302)

    def test_toggle_nonexistent_item_returns_404(self):
        """切換不存在的商品回傳 404"""
        self.client.login(username='employee1', password='pass')
        response = self.client.post(self._toggle_url(9999))
        self.assertEqual(response.status_code, 404)

    def test_only_post_method_allowed(self):
        """只允許 POST 方法"""
        self.client.login(username='employee1', password='pass')
        response = self.client.get(self._toggle_url(self.active_item.pk))
        self.assertEqual(response.status_code, 405)
