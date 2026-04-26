import json
from django.test import TestCase, Client
from django.urls import reverse
from web_app.models import User, Identity, Type, Menu


class MenuCreateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.type = Type.objects.create(type_name="炸雞")
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
        self.url = reverse("web_app:menu_create")
        self.valid_payload = {
            "name": "新品炸雞腿",
            "price": 120,
            "info": "特製醃料",
            "remark": "",
            "type_id": self.type.pk,
        }

    def test_employee_can_create_item(self):
        """員工可以新增品項"""
        self.client.login(username="employee1", password="pass")
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Menu.objects.filter(name="新品炸雞腿").exists())

    def test_admin_can_create_item(self):
        """管理員可以新增品項"""
        self.client.login(username="admin1", password="pass")
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

    def test_create_returns_new_item_data(self):
        """新增後回傳新品項的資料（含 id）"""
        self.client.login(username="employee1", password="pass")
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        data = json.loads(response.content)
        self.assertIn("id", data)
        self.assertEqual(data["name"], "新品炸雞腿")
        self.assertEqual(data["price"], 120)

    def test_customer_cannot_create_item(self):
        """顧客無法新增品項（403）"""
        self.client.login(username="customer1", password="pass")
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_create_item(self):
        """未登入無法新增品項（302）"""
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_create_with_missing_name_returns_400(self):
        """缺少 name 回傳 400"""
        self.client.login(username="employee1", password="pass")
        payload = self.valid_payload.copy()
        del payload["name"]
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_with_missing_price_returns_400(self):
        """缺少 price 回傳 400"""
        self.client.login(username="employee1", password="pass")
        payload = self.valid_payload.copy()
        del payload["price"]
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_with_missing_type_returns_400(self):
        """缺少 type_id 回傳 400"""
        self.client.login(username="employee1", password="pass")
        payload = self.valid_payload.copy()
        del payload["type_id"]
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_duplicate_name_returns_400(self):
        """名稱重複回傳 400"""
        Menu.objects.create(type=self.type, name="新品炸雞腿", price=120)
        self.client.login(username="employee1", password="pass")
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_new_item_is_active_by_default(self):
        """新增品項預設為上架狀態"""
        self.client.login(username="employee1", password="pass")
        self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        item = Menu.objects.get(name="新品炸雞腿")
        self.assertTrue(item.status)

    def test_create_with_negative_price_returns_400(self):
        """負數價格回傳 400"""
        self.client.login(username="employee1", password="pass")
        payload = self.valid_payload.copy()
        payload["price"] = -1
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_with_zero_price_is_allowed(self):
        """價格為 0 是允許的（免費品項）"""
        self.client.login(username="employee1", password="pass")
        payload = self.valid_payload.copy()
        payload["price"] = 0
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

    def test_only_post_method_allowed(self):
        """只允許 POST 方法"""
        self.client.login(username="employee1", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
