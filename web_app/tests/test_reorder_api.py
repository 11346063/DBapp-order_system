"""
ReorderAPIView（POST /api/orders/reorder/，IsCustomer）API 層測試。

Service 層（reorder_to_cart）已在 test_services_order.py 涵蓋，
此處聚焦 HTTP 層：auth、permission、序列化驗證、status code。
"""

import random

from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken

from web_app.models import Identity, Menu, Order, OrderItem, Type, User


def _make_user(identity=Identity.CUSTOMER, phone="0912345678"):
    uid = random.randint(100000, 999999)
    return User.objects.create(
        account=f"{phone}_{uid}",
        phone_number=phone,
        identity=identity,
        name="Test",
    )


def _jwt(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(user)}"}


def _make_order_with_item(user, menu):
    order = Order.objects.create(
        user=user,
        status=Order.OrderStatus.COMPLETED,
        price_total=80,
        customer_phone="0912345678",
    )
    OrderItem.objects.create(order=order, menu=menu, amount=1, total_price=80)
    return order


class ReorderAPITest(TestCase):
    URL = "/api/orders/reorder/"

    def setUp(self):
        self.customer = _make_user(Identity.CUSTOMER)
        self.staff = _make_user(Identity.EMPLOYEE, phone="0911111111")
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type, name="炸雞", price=80, status=True
        )
        self.order = _make_order_with_item(self.customer, self.menu)

    def test_customer_reorders_own_order_returns_200(self):
        resp = self.client.post(
            self.URL,
            {"order_id": self.order.pk},
            content_type="application/json",
            **_jwt(self.customer),
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertIn("added", data)
        self.assertIn("items", data)
        self.assertEqual(data["added"], 1)
        self.assertEqual(len(data["items"]), 1)

    def test_employee_identity_gets_forbidden(self):
        resp = self.client.post(
            self.URL,
            {"order_id": self.order.pk},
            content_type="application/json",
            **_jwt(self.staff),
        )
        self.assertIn(resp.status_code, [401, 403])

    def test_unauthenticated_gets_forbidden(self):
        resp = self.client.post(
            self.URL,
            {"order_id": self.order.pk},
            content_type="application/json",
        )
        self.assertIn(resp.status_code, [401, 403])

    def test_invalid_order_id_type_returns_400(self):
        resp = self.client.post(
            self.URL,
            {"order_id": "not-a-number"},
            content_type="application/json",
            **_jwt(self.customer),
        )
        self.assertEqual(resp.status_code, 400)

    def test_other_users_order_returns_404(self):
        other = _make_user(Identity.CUSTOMER, phone="0933333333")
        other_order = _make_order_with_item(other, self.menu)

        resp = self.client.post(
            self.URL,
            {"order_id": other_order.pk},
            content_type="application/json",
            **_jwt(self.customer),
        )
        self.assertEqual(resp.status_code, 404)

    def test_nonexistent_order_returns_404(self):
        resp = self.client.post(
            self.URL,
            {"order_id": 99999},
            content_type="application/json",
            **_jwt(self.customer),
        )
        self.assertEqual(resp.status_code, 404)

    def test_delisted_items_skipped_added_is_zero(self):
        self.menu.status = False
        self.menu.save(update_fields=["status"])

        resp = self.client.post(
            self.URL,
            {"order_id": self.order.pk},
            content_type="application/json",
            **_jwt(self.customer),
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["added"], 0)
        self.assertEqual(data["items"], [])
