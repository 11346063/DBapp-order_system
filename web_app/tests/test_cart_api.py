"""
CartValidatePricesAPIView（POST /api/cart/validate-prices/，AllowAny）
CartSyncPricesAPIView（POST /api/cart/sync-prices/，AllowAny）
OrderStatusAPIView POST 別名（POST /api/orders/<pk>/status/，IsEmployee）HTTP 層測試。

Service 層已在 test_services_cart.py 涵蓋，
此處聚焦 HTTP 層：format validation、status code、回應結構。
"""

import random

from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken

from web_app.models import Identity, Menu, Order, Type, User


def _make_employee(phone="0912345678"):
    uid = random.randint(100000, 999999)
    return User.objects.create(
        account=f"{phone}_{uid}",
        phone_number=phone,
        identity=Identity.EMPLOYEE,
        name="Staff",
    )


def _jwt(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(user)}"}


# ============================================================
#  CartValidatePricesAPIView
# ============================================================


class CartValidatePricesAPITest(TestCase):
    URL = "/api/cart/validate-prices/"

    def setUp(self):
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type, name="炸雞", price=80, status=True
        )

    def _item(self, price=None):
        p = price if price is not None else self.menu.price
        return {
            "menu_id": self.menu.pk,
            "name": self.menu.name,
            "base_price": p,
            "options": [],
            "options_price": 0,
            "unit_price": p,
            "quantity": 1,
            "subtotal": p,
        }

    def test_valid_cart_no_changes_returns_200(self):
        resp = self.client.post(
            self.URL,
            {"cart": [self._item()]},
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertFalse(data["has_changes"])
        self.assertEqual(data["price_changes"], [])

    def test_stale_price_detected_and_returned(self):
        resp = self.client.post(
            self.URL,
            {"cart": [self._item(price=60)]},  # DB 是 80，前端送 60
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertTrue(data["has_changes"])
        self.assertEqual(len(data["price_changes"]), 1)
        change = data["price_changes"][0]
        self.assertEqual(change["old_unit_price"], 60)
        self.assertEqual(change["new_unit_price"], 80)

    def test_empty_cart_returns_200_no_changes(self):
        resp = self.client.post(
            self.URL,
            {"cart": []},
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["data"]["has_changes"])

    def test_non_list_cart_returns_400(self):
        for bad_value in ({"menu_id": 1}, "invalid", 42, None):
            with self.subTest(bad_value=bad_value):
                resp = self.client.post(
                    self.URL,
                    {"cart": bad_value},
                    content_type="application/json",
                )
                self.assertEqual(resp.status_code, 400)

    def test_accessible_without_authentication(self):
        resp = self.client.post(
            self.URL,
            {"cart": []},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)


# ============================================================
#  CartSyncPricesAPIView
# ============================================================


class CartSyncPricesAPITest(TestCase):
    URL = "/api/cart/sync-prices/"

    def setUp(self):
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type, name="炸雞", price=80, status=True
        )

    def _item(self, price=None, qty=2):
        p = price if price is not None else self.menu.price
        return {
            "menu_id": self.menu.pk,
            "name": self.menu.name,
            "base_price": p,
            "options": [],
            "options_price": 0,
            "unit_price": p,
            "quantity": qty,
            "subtotal": p * qty,
        }

    def test_stale_prices_synced_to_db_values(self):
        resp = self.client.post(
            self.URL,
            {"cart": [self._item(price=60, qty=2)]},  # DB 是 80 → 應更新為 80
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertIn("cart", data)
        self.assertIn("total", data)
        self.assertIn("cart_count", data)
        self.assertEqual(data["cart"][0]["unit_price"], 80)
        self.assertEqual(data["total"], 160)  # 80 * 2
        self.assertEqual(data["cart_count"], 2)

    def test_empty_cart_returns_empty_result(self):
        resp = self.client.post(
            self.URL,
            {"cart": []},
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["cart"], [])
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["cart_count"], 0)

    def test_non_list_cart_returns_400(self):
        resp = self.client.post(
            self.URL,
            {"cart": "not-a-list"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_accessible_without_authentication(self):
        resp = self.client.post(
            self.URL,
            {"cart": []},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)


# ============================================================
#  OrderStatusAPIView POST 別名
# ============================================================


class OrderStatusPostAliasTest(TestCase):
    """OrderStatusAPIView POST 別名應與 PATCH 行為完全一致。"""

    def setUp(self):
        self.staff = _make_employee()

    def test_post_alias_cancels_submitted_order(self):
        order = Order.objects.create(
            status=Order.OrderStatus.SUBMITTED,
            price_total=100,
            customer_phone="0912345678",
        )

        resp = self.client.post(
            f"/api/orders/{order.pk}/status/",
            {"status": Order.OrderStatus.CANCELLED, "cancel_reason": "POST 別名測試"},
            content_type="application/json",
            **_jwt(self.staff),
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.CANCELLED)
        self.assertEqual(order.cancel_reason, "POST 別名測試")

    def test_post_alias_completes_ready_order(self):
        order = Order.objects.create(
            status=Order.OrderStatus.READY,
            price_total=100,
            customer_phone="0912345678",
        )

        resp = self.client.post(
            f"/api/orders/{order.pk}/status/",
            {"status": Order.OrderStatus.COMPLETED},
            content_type="application/json",
            **_jwt(self.staff),
        )

        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.COMPLETED)

    def test_post_alias_requires_employee_auth(self):
        order = Order.objects.create(
            status=Order.OrderStatus.SUBMITTED,
            price_total=100,
            customer_phone="0912345678",
        )

        resp = self.client.post(
            f"/api/orders/{order.pk}/status/",
            {"status": Order.OrderStatus.CANCELLED},
            content_type="application/json",
        )

        self.assertIn(resp.status_code, [401, 403])
