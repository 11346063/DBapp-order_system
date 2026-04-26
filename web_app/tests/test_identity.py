from django.test import TestCase, Client
from django.urls import reverse
from web_app.models import User, Identity, Type, Menu


class IdentityEnumTest(TestCase):
    def test_employee_value_is_E(self):
        """員工代號應為 'E'"""
        self.assertEqual(Identity.EMPLOYEE, "E")

    def test_admin_value_is_A(self):
        """管理員代號應為 'A'"""
        self.assertEqual(Identity.ADMIN, "A")

    def test_customer_value_is_C(self):
        """顧客代號應為 'C'"""
        self.assertEqual(Identity.CUSTOMER, "C")

    def test_guest_value_is_G(self):
        """訪客代號應為 'G'"""
        self.assertEqual(Identity.GUEST, "G")

    def test_guest_user_can_be_created(self):
        """可以建立 identity=GUEST 的使用者"""
        user = User.objects.create_user(
            account="guest1", password="pass", name="訪客", identity=Identity.GUEST
        )
        user.refresh_from_db()
        self.assertEqual(user.identity, Identity.GUEST)


class GuestPermissionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.type = Type.objects.create(type_name="炸雞")
        self.item = Menu.objects.create(
            type=self.type, name="炸雞排", price=70, status=True
        )
        self.guest = User.objects.create_user(
            account="guest1", password="pass", name="訪客", identity=Identity.GUEST
        )

    def test_guest_cannot_toggle_menu_status(self):
        """訪客無法切換商品上下架（403）"""
        self.client.login(username="guest1", password="pass")
        url = reverse("web_app:menu_toggle", kwargs={"pk": self.item.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_guest_cannot_edit_menu(self):
        """訪客無法編輯商品（403）"""
        import json

        self.client.login(username="guest1", password="pass")
        url = reverse("web_app:menu_edit", kwargs={"pk": self.item.pk})
        response = self.client.post(
            url,
            data=json.dumps({"name": "測試", "price": 50, "type_id": self.type.pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_guest_sees_only_active_items(self):
        """訪客只能看到上架商品（與顧客相同）"""
        Menu.objects.create(type=self.type, name="已下架品項", price=50, status=False)
        self.client.login(username="guest1", password="pass")
        response = self.client.get(reverse("web_app:home"))
        menus = response.context["menus"]
        names = [m.name for m in menus]
        self.assertIn("炸雞排", names)
        self.assertNotIn("已下架品項", names)
