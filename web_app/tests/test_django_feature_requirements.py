import json

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from web_app.models import Menu, Order, Type


class RequestResponseDemoTest(TestCase):
    def test_demo_endpoint_returns_request_and_session_data(self):
        session = self.client.session
        session["cart"] = [{"quantity": 2}, {"quantity": 3}]
        session.save()

        response = self.client.get(reverse("web_app:request_response_demo"), {"foo": "bar"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["method"], "GET")
        self.assertEqual(payload["query"], {"foo": "bar"})
        self.assertEqual(payload["cart_count"], 5)
        self.assertFalse(payload["is_authenticated"])


class ApiExceptionHandlingTest(TestCase):
    def test_cart_add_rejects_invalid_json_with_400(self):
        response = self.client.post(
            reverse("web_app:cart_add"),
            data="{bad json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "JSON 格式錯誤")

    def test_cart_add_rejects_missing_required_field_with_400(self):
        response = self.client.post(
            reverse("web_app:cart_add"),
            data=json.dumps({"menu_id": 1, "name": "雞排"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("缺少必要欄位", response.json()["error"])


class MenuSearchPaginationTest(TestCase):
    def setUp(self):
        self.type = Type.objects.create(type_name="主餐")
        for index in range(13):
            Menu.objects.create(
                type=self.type,
                name=f"招牌炸雞 {index:02d}",
                price=80 + index,
                info="人氣餐點",
                status=True,
            )
        Menu.objects.create(
            type=self.type,
            name="蜂蜜鬆餅",
            price=120,
            info="甜點",
            status=True,
        )

    def test_home_search_filters_menu_items(self):
        response = self.client.get(reverse("web_app:home"), {"q": "鬆餅"})

        self.assertContains(response, "蜂蜜鬆餅")
        self.assertNotContains(response, "招牌炸雞 00")
        self.assertEqual(response.context["search_query"], "鬆餅")

    def test_home_paginates_menu_items(self):
        response = self.client.get(reverse("web_app:home"))

        self.assertEqual(response.context["paginator"].per_page, 12)
        self.assertTrue(response.context["page_obj"].has_next())
        self.assertContains(response, "下一頁")


class OrderSignalTest(TestCase):
    def test_order_creation_signal_logs_event(self):
        with self.assertLogs("web_app.signals", level="INFO") as logs:
            Order.objects.create(
                create_time=timezone.now(),
                status=0,
                price_total=100,
            )

        self.assertTrue(any("Order created" in message for message in logs.output))


class InternationalizationSettingsTest(TestCase):
    @override_settings(LANGUAGE_CODE="zh-hant")
    def test_set_language_url_is_available(self):
        response = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": reverse("web_app:home")},
        )

        self.assertEqual(response.status_code, 302)

