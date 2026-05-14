from django.test import TestCase, Client
from django.urls import reverse
from web_app.models import User, Identity, Type, Menu


class HomeViewFilterTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.type = Type.objects.create(type_name="炸雞")
        self.active_item = Menu.objects.create(
            type=self.type,
            name="香脆炸雞",
            price=80,
            status=True,
        )
        self.inactive_item = Menu.objects.create(
            type=self.type,
            name="已售完品項",
            price=100,
            status=False,
        )
        self.customer = User.objects.create_user(
            account="customer1",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
        )
        self.employee = User.objects.create_user(
            account="employee1",
            password="pass",
            name="員工",
            identity=Identity.EMPLOYEE,
        )
        self.admin = User.objects.create_user(
            account="admin1", password="pass", name="管理員", identity=Identity.ADMIN
        )
        self.url = reverse("web_app:home")

    def test_anonymous_user_sees_only_active_items(self):
        """未登入使用者只看到上架商品"""
        response = self.client.get(self.url)
        menus = response.context["menus"]
        self.assertIn(self.active_item, menus)
        self.assertNotIn(self.inactive_item, menus)

    def test_customer_sees_only_active_items(self):
        """顧客只看到上架商品"""
        self.client.login(username="customer1", password="pass")
        response = self.client.get(self.url)
        menus = response.context["menus"]
        self.assertIn(self.active_item, menus)
        self.assertNotIn(self.inactive_item, menus)

    def test_employee_sees_all_items(self):
        """員工可以看到所有商品（含下架）"""
        self.client.login(username="employee1", password="pass")
        response = self.client.get(self.url)
        menus = response.context["menus"]
        self.assertIn(self.active_item, menus)
        self.assertIn(self.inactive_item, menus)

    def test_admin_sees_all_items(self):
        """管理員可以看到所有商品（含下架）"""
        self.client.login(username="admin1", password="pass")
        response = self.client.get(self.url)
        menus = response.context["menus"]
        self.assertIn(self.active_item, menus)
        self.assertIn(self.inactive_item, menus)

    def test_context_has_is_staff_false_for_customer(self):
        """顧客的 context 中 is_staff 為 False"""
        self.client.login(username="customer1", password="pass")
        response = self.client.get(self.url)
        self.assertFalse(response.context["is_staff"])

    def test_context_has_is_staff_true_for_employee(self):
        """員工的 context 中 is_staff 為 True"""
        self.client.login(username="employee1", password="pass")
        response = self.client.get(self.url)
        self.assertTrue(response.context["is_staff"])

    def test_context_has_is_staff_true_for_admin(self):
        """管理員的 context 中 is_staff 為 True"""
        self.client.login(username="admin1", password="pass")
        response = self.client.get(self.url)
        self.assertTrue(response.context["is_staff"])

    def test_employee_cannot_manage_menu_items(self):
        """員工不能看到新增品項與編輯品項入口"""
        self.client.login(username="employee1", password="pass")
        response = self.client.get(self.url)
        self.assertTrue(response.context["is_staff"])
        self.assertFalse(response.context["can_manage_menu"])
        self.assertNotContains(response, "新增品項")
        self.assertNotContains(response, "編輯品項")

    def test_employee_assisted_ordering_sees_only_active_items(self):
        """員工代客點餐頁只顯示上架商品，不混入管理操作"""
        self.client.login(username="employee1", password="pass")
        response = self.client.get(reverse("web_app:assisted_ordering"))
        menus = response.context["menus"]
        self.assertIn(self.active_item, menus)
        self.assertNotIn(self.inactive_item, menus)
        self.assertFalse(response.context["is_staff"])
        self.assertFalse(response.context["can_manage_menu"])
        self.assertTrue(response.context["is_assisted_ordering"])
        self.assertContains(response, "assisted-item-card")
        self.assertContains(response, 'data-assisted-delta="-1"')
        self.assertContains(response, 'data-assisted-delta="1"')
        self.assertNotContains(response, "card-img-top-placeholder")
        self.assertNotContains(response, "加入購物車")
        self.assertNotContains(response, "編輯品項")

    def test_anonymous_cannot_access_assisted_ordering(self):
        """非員工不可進入代客點餐頁"""
        response = self.client.get(reverse("web_app:assisted_ordering"))
        self.assertRedirects(response, reverse("web_app:home"))

    def test_admin_can_manage_menu_items(self):
        """管理員可以看到新增品項與編輯品項入口"""
        self.client.login(username="admin1", password="pass")
        response = self.client.get(self.url)
        self.assertTrue(response.context["can_manage_menu"])
        self.assertContains(response, "新增品項")
        self.assertContains(response, "編輯品項")

    def test_context_has_is_staff_false_for_anonymous(self):
        """未登入使用者的 context 中 is_staff 為 False"""
        response = self.client.get(self.url)
        self.assertFalse(response.context["is_staff"])
