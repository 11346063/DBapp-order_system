"""
功能 23：顧客取消未接單訂單測試。

涵蓋 service 層 `customer_cancel_order` 與 API `CustomerCancelOrderAPIView`
（`/api/orders/<id>/customer-cancel/`, AllowAny）。
WebSocket 通知不需 mock：`_notify_*` 已 try/except 且 channel_layer 為 None 時短路。
"""

import random

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from web_app.models import Identity, Order, User
from web_app.services import order as order_service
from web_app.services.exceptions import (
    NotFoundError,
    PermissionBusinessError,
    ValidationServiceError,
)


def _make_user(identity=Identity.CUSTOMER, phone="0912345678"):
    uid = random.randint(100000, 999999)
    return User.objects.create(
        account=f"{phone}_{uid}",
        phone_number=phone,
        identity=identity,
        name="Test",
    )


def _make_order(status=Order.OrderStatus.SUBMITTED, user=None):
    return Order.objects.create(
        status=status,
        price_total=100,
        customer_phone="0912345678",
        user=user,
    )


class CustomerCancelServiceTest(TestCase):
    def setUp(self):
        self.customer = _make_user(Identity.CUSTOMER)

    def test_authenticated_customer_cancels_own_submitted_order(self):
        order = _make_order(Order.OrderStatus.SUBMITTED, user=self.customer)

        order_service.customer_cancel_order(order.pk, self.customer, {})

        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.CANCELLED)
        self.assertEqual(order.cancel_reason, "顧客主動取消")

    def test_guest_cancels_order_held_in_session(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)
        session = {"last_order_id": order.pk}

        order_service.customer_cancel_order(order.pk, AnonymousUser(), session)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.CANCELLED)
        self.assertEqual(order.cancel_reason, "顧客主動取消")

    def test_authenticated_customer_cannot_cancel_others_order(self):
        other = _make_user(Identity.CUSTOMER, phone="0911111111")
        order = _make_order(Order.OrderStatus.SUBMITTED, user=other)

        with self.assertRaises(PermissionBusinessError):
            order_service.customer_cancel_order(order.pk, self.customer, {})

        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.SUBMITTED)

    def test_guest_without_session_ownership_is_denied(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)

        with self.assertRaises(PermissionBusinessError):
            order_service.customer_cancel_order(order.pk, AnonymousUser(), {})

        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.SUBMITTED)

    def test_cannot_cancel_non_submitted_orders(self):
        for status in (
            Order.OrderStatus.ACCEPTED,
            Order.OrderStatus.READY,
            Order.OrderStatus.COMPLETED,
            Order.OrderStatus.CANCELLED,
        ):
            order = _make_order(status, user=self.customer)
            with self.assertRaises(ValidationServiceError):
                order_service.customer_cancel_order(order.pk, self.customer, {})
            order.refresh_from_db()
            self.assertEqual(order.status, status)

    def test_missing_order_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            order_service.customer_cancel_order(999999, self.customer, {})


class CustomerCancelApiTest(TestCase):
    def setUp(self):
        self.customer = _make_user(Identity.CUSTOMER)

    def test_logged_in_customer_cancels_own_order(self):
        order = _make_order(Order.OrderStatus.SUBMITTED, user=self.customer)
        self.client.force_login(self.customer)

        resp = self.client.post(f"/api/orders/{order.pk}/customer-cancel/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")
        self.assertEqual(resp.json()["message"], "訂單已取消")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.CANCELLED)

    def test_cancelling_others_order_is_forbidden(self):
        other = _make_user(Identity.CUSTOMER, phone="0911111111")
        order = _make_order(Order.OrderStatus.SUBMITTED, user=other)
        self.client.force_login(self.customer)

        resp = self.client.post(f"/api/orders/{order.pk}/customer-cancel/")

        self.assertEqual(resp.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.SUBMITTED)
