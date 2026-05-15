import json
import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from web_app.models import User, Identity, Type, Menu


class MenuEditTest(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()
        self.client = Client()
        self.type = Type.objects.create(type_name="炸雞")
        self.other_type = Type.objects.create(type_name="飲料")
        self.item = Menu.objects.create(
            type=self.type,
            name="香脆炸雞",
            price=80,
            info="好吃",
            remark="限量",
            status=True,
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
        self.url = reverse("web_app:menu_edit", kwargs={"pk": self.item.pk})
        self.valid_payload = {
            "name": "超脆炸雞",
            "price": 90,
            "info": "更好吃",
            "remark": "每日限量",
            "type_id": self.type.pk,
        }

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_employee_cannot_edit_item(self):
        """員工無法編輯品項"""
        self.client.login(username="employee1", password="pass")
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, "香脆炸雞")
        self.assertEqual(self.item.price, 80)

    def test_admin_can_edit_item(self):
        """管理員可以編輯品項"""
        self.client.login(username="admin1", password="pass")
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

    def test_edit_returns_updated_data(self):
        """編輯後回傳更新後的資料"""
        self.client.login(username="admin1", password="pass")
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        data = json.loads(response.content)
        self.assertEqual(data["data"]["name"], "超脆炸雞")
        self.assertEqual(data["data"]["price"], 90)
        self.assertEqual(data["data"]["image_url"], "")

    def test_edit_with_image_upload_updates_file(self):
        """編輯品項可更新照片"""
        self.client.login(username="admin1", password="pass")
        image = SimpleUploadedFile(
            "crispy.png",
            b"fake-image-content",
            content_type="image/png",
        )
        response = self.client.post(
            self.url,
            data={**self.valid_payload, "file_path": image},
        )
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertTrue(self.item.file_path.name.startswith("image/crispy"))
        data = json.loads(response.content)
        self.assertIn("/media/image/crispy", data["data"]["image_url"])

    def test_edit_without_image_keeps_existing_file(self):
        """未選新照片時保留原本照片"""
        self.item.file_path = "image/original.png"
        self.item.save(update_fields=["file_path"])
        self.client.login(username="admin1", password="pass")
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.file_path.name, "image/original.png")

    def test_customer_cannot_edit_item(self):
        """顧客無法編輯品項（403）"""
        self.client.login(username="customer1", password="pass")
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_edit_item(self):
        """未登入無法編輯品項（401）"""
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_edit_with_missing_name_returns_400(self):
        """缺少必填欄位 name 回傳 400"""
        self.client.login(username="admin1", password="pass")
        payload = self.valid_payload.copy()
        del payload["name"]
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_with_missing_price_returns_400(self):
        """缺少必填欄位 price 回傳 400"""
        self.client.login(username="admin1", password="pass")
        payload = self.valid_payload.copy()
        del payload["price"]
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_nonexistent_item_returns_404(self):
        """編輯不存在的品項回傳 404"""
        self.client.login(username="admin1", password="pass")
        url = reverse("web_app:menu_edit", kwargs={"pk": 9999})
        response = self.client.post(
            url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_edit_can_change_type(self):
        """可以修改品項的分類"""
        self.client.login(username="admin1", password="pass")
        payload = self.valid_payload.copy()
        payload["type_id"] = self.other_type.pk
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.type_id, self.other_type.pk)

    def test_edit_with_negative_price_returns_400(self):
        """負數價格回傳 400"""
        self.client.login(username="admin1", password="pass")
        payload = self.valid_payload.copy()
        payload["price"] = -1
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_with_zero_price_is_allowed(self):
        """價格為 0 是允許的（免費品項）"""
        self.client.login(username="admin1", password="pass")
        payload = self.valid_payload.copy()
        payload["price"] = 0
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

    def test_only_post_method_allowed(self):
        """只允許 POST 方法"""
        self.client.login(username="admin1", password="pass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
