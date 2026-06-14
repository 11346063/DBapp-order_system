"""
營業時間控制測試。

- is_store_open：純函式，含跨午夜情境（SimpleTestCase）。
- 結帳擋單：非營業時段擋顧客、放行員工代客、營業中放行（TestCase）。
- update_settings：營業時間欄位可被儲存。
"""

import random
from datetime import datetime, time
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from web_app.models import Identity, Menu, Type, User
from web_app.services import order as order_service
from web_app.services import store_settings as settings_service
from web_app.services.exceptions import ValidationServiceError
from web_app.services.store_settings import is_store_open


def _settings(enabled, open_t, close_t):
    return SimpleNamespace(
        business_hours_enabled=enabled, open_time=open_t, close_time=close_t
    )


def _make_user(identity=Identity.CUSTOMER, phone="0912345678"):
    uid = random.randint(100000, 999999)
    return User.objects.create(
        account=f"{phone}_{uid}", phone_number=phone, identity=identity, name="Test"
    )


class IsStoreOpenTest(SimpleTestCase):
    def test_disabled_is_always_open(self):
        s = _settings(False, time(10, 0), time(11, 0))
        self.assertTrue(is_store_open(s, now=datetime(2026, 6, 14, 3, 0)))

    def test_within_window(self):
        s = _settings(True, time(10, 0), time(21, 0))
        self.assertTrue(is_store_open(s, now=datetime(2026, 6, 14, 12, 0)))

    def test_before_open(self):
        s = _settings(True, time(10, 0), time(21, 0))
        self.assertFalse(is_store_open(s, now=datetime(2026, 6, 14, 9, 0)))

    def test_after_close(self):
        s = _settings(True, time(10, 0), time(21, 0))
        self.assertFalse(is_store_open(s, now=datetime(2026, 6, 14, 22, 0)))

    def test_overnight_window(self):
        s = _settings(True, time(18, 0), time(2, 0))
        self.assertTrue(is_store_open(s, now=datetime(2026, 6, 14, 23, 0)))
        self.assertTrue(is_store_open(s, now=datetime(2026, 6, 14, 1, 0)))
        self.assertFalse(is_store_open(s, now=datetime(2026, 6, 14, 10, 0)))


class CheckoutBusinessHoursGuardTest(TestCase):
    def setUp(self):
        self.type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(type=self.type, name="雞排", price=80)
        self.cart = [
            {"menu_id": self.menu.pk, "quantity": 1, "subtotal": 80, "options": []}
        ]

    def _patch_cart(self):
        return patch.multiple(
            "web_app.services.order.cart_service",
            ensure_prices_current=lambda *a, **k: None,
            get_cart=lambda *a, **k: self.cart,
            cart_total=lambda *a, **k: 80,
            clear_cart=lambda *a, **k: None,
        )

    @patch("web_app.services.order.is_store_open", return_value=False)
    def test_customer_blocked_outside_hours(self, _mock):
        customer = _make_user(Identity.CUSTOMER)
        with self._patch_cart():
            with self.assertRaisesMessage(ValidationServiceError, "非營業時間"):
                order_service.create_order_from_cart(
                    customer, {}, {"customer_phone": "0912345678"}
                )

    @patch("web_app.services.order.is_store_open", return_value=False)
    def test_staff_can_order_outside_hours(self, _mock):
        staff = _make_user(Identity.EMPLOYEE, phone="0922222222")
        with self._patch_cart():
            order = order_service.create_order_from_cart(
                staff, {}, {"customer_phone": "0933333333"}
            )
        self.assertEqual(order.status, order_service.Order.OrderStatus.ACCEPTED)

    @patch("web_app.services.order.is_store_open", return_value=True)
    def test_customer_allowed_within_hours(self, _mock):
        customer = _make_user(Identity.CUSTOMER)
        with self._patch_cart():
            order = order_service.create_order_from_cart(
                customer, {}, {"customer_phone": "0912345678"}
            )
        self.assertEqual(order.status, order_service.Order.OrderStatus.SUBMITTED)


class IsStoreOpenLiveClockTest(TestCase):
    """USE_TZ=False 下，不帶 now 走 timezone.now() 不可拋 naive datetime 例外。"""

    def test_enabled_without_now_does_not_raise(self):
        s = settings_service.get_settings()
        s.business_hours_enabled = True
        s.open_time = time(0, 0)
        s.close_time = time(23, 59)
        s.save(update_fields=["business_hours_enabled", "open_time", "close_time"])
        # 不傳 now：使用伺服器時鐘，需正常回傳 bool 而非拋例外
        self.assertIsInstance(settings_service.is_store_open(s), bool)


class HomeViewWhenClosedTest(TestCase):
    """休息中時首頁仍須正常顯示菜單（顧客只是無法下單，不應 500）。"""

    def setUp(self):
        self.type = Type.objects.create(type_name="炸雞")
        self.menu = Menu.objects.create(
            type=self.type, name="香脆炸雞", price=80, status=True
        )

    @patch("web_app.views.home.settings_service.is_store_open", return_value=False)
    def test_menu_visible_with_banner_when_closed(self, _mock):
        from django.urls import reverse

        resp = self.client.get(reverse("web_app:home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "香脆炸雞")
        self.assertContains(resp, "非營業時間")


class UpdateBusinessHoursTest(TestCase):
    def test_update_persists_business_hours(self):
        settings_service.update_settings(
            {
                "extra_ingredient_cost": 10,
                "option_name_spicy": "辣度",
                "option_name_garlic": "加蒜",
                "option_name_basil": "九層塔",
                "option_name_cut": "切",
                "business_hours_enabled": True,
                "open_time": time(9, 0),
                "close_time": time(20, 0),
            }
        )
        s = settings_service.get_settings()
        self.assertTrue(s.business_hours_enabled)
        self.assertEqual(s.open_time, time(9, 0))
        self.assertEqual(s.close_time, time(20, 0))
