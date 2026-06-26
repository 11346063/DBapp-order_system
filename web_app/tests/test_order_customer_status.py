"""
OrderCustomerStatusAPIView（GET /api/orders/<pk>/customer-status/，AllowAny）測試。

驗證邏輯：
  - 登入顧客為訂單擁有者 → 200，回傳狀態欄位
  - 登入顧客非擁有者 → 403
  - 訪客 session["last_order_id"] 符合 → 200
  - 訪客 session["last_order_id"] 不符或缺失 → 403
  - 訂單不存在 → 404
  - 回應含 cancel_reason 欄位（取消訂單時有值）
"""

import random

from django.test import TestCase

from web_app.models import Identity, Order, User


def _make_user(identity=Identity.CUSTOMER, phone="0912345678"):
    uid = random.randint(100000, 999999)
    return User.objects.create(
        account=f"{phone}_{uid}",
        phone_number=phone,
        identity=identity,
        name="Test",
    )


def _make_order(user=None, status=Order.OrderStatus.SUBMITTED):
    return Order.objects.create(
        user=user,
        status=status,
        price_total=100,
        customer_phone="0912345678",
        pickup_code="678",
        estimated_wait_minutes=20,
    )


class OrderCustomerStatusAPITest(TestCase):
    URL = "/api/orders/{pk}/customer-status/"

    def setUp(self):
        self.customer = _make_user(Identity.CUSTOMER)

    # ------------------------------------------------------------------
    # 登入顧客
    # ------------------------------------------------------------------

    def test_owner_gets_200_with_required_fields(self):
        order = _make_order(user=self.customer, status=Order.OrderStatus.ACCEPTED)
        self.client.force_login(self.customer)

        resp = self.client.get(self.URL.format(pk=order.pk))

        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertIn("order_status", data)
        self.assertIn("estimated_wait_minutes", data)
        self.assertIn("pickup_code", data)
        self.assertIn("cancel_reason", data)
        self.assertEqual(data["order_status"], Order.OrderStatus.ACCEPTED)
        self.assertEqual(data["pickup_code"], "678")
        self.assertEqual(data["estimated_wait_minutes"], 20)

    def test_non_owner_gets_403(self):
        other = _make_user(Identity.CUSTOMER, phone="0911111111")
        order = _make_order(user=other)
        self.client.force_login(self.customer)

        resp = self.client.get(self.URL.format(pk=order.pk))

        self.assertEqual(resp.status_code, 403)

    def test_status_field_matches_order_for_each_status(self):
        for status in (
            Order.OrderStatus.SUBMITTED,
            Order.OrderStatus.ACCEPTED,
            Order.OrderStatus.READY,
            Order.OrderStatus.COMPLETED,
        ):
            with self.subTest(status=status):
                order = _make_order(user=self.customer, status=status)
                self.client.force_login(self.customer)

                resp = self.client.get(self.URL.format(pk=order.pk))

                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp.json()["data"]["order_status"], status)

    # ------------------------------------------------------------------
    # 訪客（session 驗證）
    # ------------------------------------------------------------------

    def test_guest_with_matching_session_gets_200(self):
        order = _make_order()
        session = self.client.session
        session["last_order_id"] = order.pk
        session.save()

        resp = self.client.get(self.URL.format(pk=order.pk))

        self.assertEqual(resp.status_code, 200)
        self.assertIn("order_status", resp.json()["data"])

    def test_guest_without_session_gets_403(self):
        order = _make_order()

        resp = self.client.get(self.URL.format(pk=order.pk))

        self.assertEqual(resp.status_code, 403)

    def test_guest_mismatched_session_gets_403(self):
        order = _make_order()
        session = self.client.session
        session["last_order_id"] = order.pk + 999
        session.save()

        resp = self.client.get(self.URL.format(pk=order.pk))

        self.assertEqual(resp.status_code, 403)

    # ------------------------------------------------------------------
    # 404
    # ------------------------------------------------------------------

    def test_nonexistent_order_returns_404(self):
        self.client.force_login(self.customer)

        resp = self.client.get(self.URL.format(pk=99999))

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["status"], "error")

    # ------------------------------------------------------------------
    # cancel_reason 欄位
    # ------------------------------------------------------------------

    def test_cancelled_order_includes_cancel_reason(self):
        order = _make_order(user=self.customer, status=Order.OrderStatus.CANCELLED)
        order.cancel_reason = "食材用完"
        order.save(update_fields=["cancel_reason"])
        self.client.force_login(self.customer)

        resp = self.client.get(self.URL.format(pk=order.pk))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["cancel_reason"], "食材用完")
