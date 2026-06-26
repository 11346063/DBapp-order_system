"""
MenuDetailAPIView（GET /api/menu/<pk>/，AllowAny）及 get_menu_detail service 測試。
"""

from django.test import TestCase

from web_app.models import Menu, Options, Type
from web_app.services import menu as menu_service
from web_app.services.exceptions import NotFoundError


class GetMenuDetailServiceTest(TestCase):
    def setUp(self):
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type,
            name="香脆炸雞",
            price=80,
            info="外皮酥脆",
            remark="可加辣",
            status=True,
        )

    def test_returns_menu_by_id(self):
        result = menu_service.get_menu_detail(self.menu.pk)

        self.assertEqual(result.pk, self.menu.pk)
        self.assertEqual(result.name, "香脆炸雞")
        self.assertEqual(result.price, 80)

    def test_select_related_type_available(self):
        result = menu_service.get_menu_detail(self.menu.pk)

        self.assertEqual(result.type.type_name, "主餐")

    def test_raises_not_found_for_missing_id(self):
        with self.assertRaises(NotFoundError):
            menu_service.get_menu_detail(99999)


class MenuDetailAPITest(TestCase):
    URL = "/api/menu/{pk}/"

    def setUp(self):
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type,
            name="香脆炸雞",
            price=80,
            info="外皮酥脆",
            remark="可加辣",
            status=True,
        )

    def test_returns_200_with_menu_data(self):
        resp = self.client.get(self.URL.format(pk=self.menu.pk))

        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["id"], self.menu.pk)
        self.assertEqual(data["name"], "香脆炸雞")
        self.assertEqual(data["price"], 80)
        self.assertEqual(data["type_name"], "主餐")
        self.assertEqual(data["info"], "外皮酥脆")

    def test_returns_404_for_nonexistent_menu(self):
        resp = self.client.get(self.URL.format(pk=99999))

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["status"], "error")

    def test_accessible_without_authentication(self):
        """AllowAny — 無需登入即可取得菜單詳情"""
        resp = self.client.get(self.URL.format(pk=self.menu.pk))

        self.assertEqual(resp.status_code, 200)

    def test_response_includes_options_list(self):
        resp = self.client.get(self.URL.format(pk=self.menu.pk))

        self.assertIn("options", resp.json()["data"])
        self.assertIsInstance(resp.json()["data"]["options"], list)

    def test_options_list_contains_linked_options(self):
        opt, _ = Options.objects.get_or_create(name="小辣", defaults={"price": 0})
        self.menu.options.add(opt)

        resp = self.client.get(self.URL.format(pk=self.menu.pk))

        option_names = [o["name"] for o in resp.json()["data"]["options"]]
        self.assertIn("小辣", option_names)
