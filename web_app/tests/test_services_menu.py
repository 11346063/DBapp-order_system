from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from web_app.models import Identity, Menu, Type, User
from web_app.services import menu as menu_service
from web_app.services.exceptions import NotFoundError, ValidationServiceError


class MenuServiceTest(TestCase):
    def setUp(self):
        self.type = Type.objects.create(type_name="主餐")
        self.other_type = Type.objects.create(type_name="飲料")
        self.menu = Menu.objects.create(
            type=self.type,
            name="香脆炸雞",
            price=80,
            info="好吃",
            remark="限量",
            status=True,
        )
        self.admin = User.objects.create_user(
            account="menu_admin",
            password="pass",
            name="管理員",
            identity=Identity.ADMIN,
        )
        self.customer = User.objects.create_user(
            account="menu_customer",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
        )

    def test_toggle_menu_status_returns_new_status(self):
        result = menu_service.toggle_menu_status(self.menu.pk)

        self.menu.refresh_from_db()
        self.assertEqual(result, {"status": False, "name": "香脆炸雞"})
        self.assertFalse(self.menu.status)

    def test_toggle_missing_menu_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            menu_service.toggle_menu_status(9999)

    def test_create_menu_item_validates_required_fields(self):
        with self.assertRaisesMessage(ValidationServiceError, "名稱、價格、分類為必填"):
            menu_service.create_menu_item({"name": "新品"})

    def test_create_menu_item_rejects_duplicate_name(self):
        with self.assertRaisesMessage(ValidationServiceError, "品項名稱已存在"):
            menu_service.create_menu_item(
                {"name": "香脆炸雞", "price": 80, "type_id": self.type.pk}
            )

    def test_create_menu_item_accepts_zero_price(self):
        menu = menu_service.create_menu_item(
            {
                "name": "免費湯品",
                "price": 0,
                "type_id": self.type.pk,
                "info": "今日限定",
            }
        )

        self.assertEqual(menu.price, 0)
        self.assertTrue(menu.status)
        self.assertEqual(menu.info, "今日限定")

    def test_update_menu_item_changes_type_and_keeps_status(self):
        menu = menu_service.update_menu_item(
            self.menu.pk,
            {
                "name": "超脆炸雞",
                "price": "90",
                "type_id": self.other_type.pk,
                "info": "更好吃",
                "remark": "",
            },
        )

        self.assertEqual(menu.name, "超脆炸雞")
        self.assertEqual(menu.price, 90)
        self.assertEqual(menu.type, self.other_type)
        self.assertTrue(menu.status)

    def test_validate_uploaded_image_rejects_non_image(self):
        upload = SimpleUploadedFile(
            "notes.txt",
            b"not an image",
            content_type="text/plain",
        )

        with self.assertRaisesMessage(ValidationServiceError, "圖片格式不正確"):
            menu_service.validate_uploaded_image(upload)

    def test_visible_menus_for_customer_hides_inactive_items(self):
        Menu.objects.create(
            type=self.type,
            name="隱藏品項",
            price=100,
            status=False,
        )

        menus = list(menu_service.visible_menus_for_user(self.customer))

        self.assertEqual([menu.name for menu in menus], ["香脆炸雞"])

    def test_visible_menus_for_staff_includes_inactive_items(self):
        Menu.objects.create(
            type=self.type,
            name="隱藏品項",
            price=100,
            status=False,
        )

        menus = list(menu_service.visible_menus_for_user(self.admin))

        self.assertEqual({menu.name for menu in menus}, {"香脆炸雞", "隱藏品項"})
