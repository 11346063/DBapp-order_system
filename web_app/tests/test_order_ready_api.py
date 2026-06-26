"""
OrderReadyAPIView（POST /api/orders/<pk>/ready/，IsEmployee）API 層測試。

Service 層（mark_order_ready）已在 test_order_acceptance.py 的
MarkOrderReadyServiceTest 涵蓋，此處聚焦 HTTP 層：auth、permission、status code。
"""

import random

from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken

from web_app.models import Identity, Order, User


def _make_user(identity=Identity.EMPLOYEE, phone="0912345678"):
    uid = random.randint(100000, 999999)
    return User.objects.create(
        account=f"{phone}_{uid}",
        phone_number=phone,
        identity=identity,
        name="Test",
    )


def _make_order(status=Order.OrderStatus.ACCEPTED):
    return Order.objects.create(
        status=status,
        price_total=100,
        customer_phone="0912345678",
    )


def _jwt(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(user)}"}


class OrderReadyAPITest(TestCase):
    URL = "/api/orders/{pk}/ready/"

    def setUp(self):
        self.staff = _make_user(Identity.EMPLOYEE)
        self.customer = _make_user(Identity.CUSTOMER, phone="0911111111")

    def test_employee_marks_accepted_order_ready(self):
        order = _make_order(Order.OrderStatus.ACCEPTED)

        resp = self.client.post(self.URL.format(pk=order.pk), **_jwt(self.staff))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.READY)
        self.assertIsNotNone(order.ready_at)

    def test_admin_can_also_mark_order_ready(self):
        admin = _make_user(Identity.ADMIN, phone="0922222222")
        order = _make_order(Order.OrderStatus.ACCEPTED)

        resp = self.client.post(self.URL.format(pk=order.pk), **_jwt(admin))

        self.assertEqual(resp.status_code, 200)

    def test_non_accepted_order_returns_400(self):
        for status in (
            Order.OrderStatus.SUBMITTED,
            Order.OrderStatus.READY,
            Order.OrderStatus.COMPLETED,
            Order.OrderStatus.CANCELLED,
        ):
            with self.subTest(status=status):
                order = _make_order(status)
                resp = self.client.post(
                    self.URL.format(pk=order.pk), **_jwt(self.staff)
                )
                self.assertEqual(resp.status_code, 400)
                order.refresh_from_db()
                self.assertEqual(order.status, status)

    def test_unauthenticated_returns_401_or_403(self):
        order = _make_order()

        resp = self.client.post(self.URL.format(pk=order.pk))

        self.assertIn(resp.status_code, [401, 403])

    def test_customer_identity_gets_403(self):
        order = _make_order()

        resp = self.client.post(self.URL.format(pk=order.pk), **_jwt(self.customer))

        self.assertIn(resp.status_code, [401, 403])

    def test_nonexistent_order_returns_404(self):
        resp = self.client.post(self.URL.format(pk=99999), **_jwt(self.staff))

        self.assertEqual(resp.status_code, 404)

    def test_response_includes_status_counts(self):
        order = _make_order(Order.OrderStatus.ACCEPTED)

        resp = self.client.post(self.URL.format(pk=order.pk), **_jwt(self.staff))

        self.assertEqual(resp.status_code, 200)
        self.assertIn("status_counts", resp.json()["data"])
