"""
StaffOrderCreateAPIView（POST /api/v1/orders/staff/，IsEmployee）
及 create_staff_order_from_items service 測試。

涵蓋：
  Service：成功建立 ACCEPTED 訂單、缺電話、空品項、無效 menu_id、今日售完、下架品項
  API：201 成功、401/403 未授權、400 各驗證錯誤
"""

import random
from datetime import date

from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken

from web_app.models import Identity, Menu, Order, OrderItem, Type, User
from web_app.services import order as order_service
from web_app.tests.test_helpers import seed_system_options
from web_app.services.exceptions import (
    EmptyCartError,
    StaffCustomerPhoneRequired,
    ValidationServiceError,
)


def _make_user(identity=Identity.EMPLOYEE, phone="0912345678"):
    uid = random.randint(100000, 999999)
    return User.objects.create(
        account=f"{phone}_{uid}",
        phone_number=phone,
        identity=identity,
        name="Test",
    )


def _jwt(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(user)}"}


# ============================================================
#  Service 層
# ============================================================


class StaffOrderCreateServiceTest(TestCase):
    def setUp(self):
        seed_system_options()
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type, name="炸雞", price=80, status=True
        )
        self.staff = _make_user(Identity.EMPLOYEE)

    def _data(self, **overrides):
        data = {
            "customer_phone": "0912345678",
            "spicy_level": "不辣",
            "extra_garlic_qty": 0,
            "extra_basil_qty": 0,
            "remark": "",
            "custom_options": [],
            "items": [{"menu_id": self.menu.pk, "qty": 1, "options": []}],
        }
        data.update(overrides)
        return data

    def test_creates_accepted_order_with_pickup_code(self):
        order = order_service.create_staff_order_from_items(self.staff, self._data())

        self.assertEqual(order.status, Order.OrderStatus.ACCEPTED)
        self.assertIsNotNone(order.accepted_at)
        self.assertTrue(order.pickup_code)
        self.assertEqual(order.customer_phone, "0912345678")
        self.assertEqual(order.user, self.staff)

    def test_order_item_created_with_correct_amount(self):
        order = order_service.create_staff_order_from_items(
            self.staff,
            self._data(items=[{"menu_id": self.menu.pk, "qty": 3, "options": []}]),
        )

        item = OrderItem.objects.get(order=order)
        self.assertEqual(item.amount, 3)
        self.assertEqual(item.total_price, 240)  # 80 * 3

    def test_price_total_calculated_from_item_quantities(self):
        order = order_service.create_staff_order_from_items(
            self.staff,
            self._data(items=[{"menu_id": self.menu.pk, "qty": 2, "options": []}]),
        )

        self.assertEqual(order.price_total, 160)  # 80 * 2

    def test_missing_phone_raises_staff_phone_required(self):
        with self.assertRaises(StaffCustomerPhoneRequired):
            order_service.create_staff_order_from_items(
                self.staff, self._data(customer_phone="")
            )

    def test_empty_items_raises_empty_cart_error(self):
        with self.assertRaises(EmptyCartError):
            order_service.create_staff_order_from_items(
                self.staff, self._data(items=[])
            )

    def test_invalid_menu_id_raises_validation_error(self):
        with self.assertRaises(ValidationServiceError):
            order_service.create_staff_order_from_items(
                self.staff,
                self._data(items=[{"menu_id": 99999, "qty": 1, "options": []}]),
            )

    def test_inactive_menu_raises_validation_error(self):
        self.menu.status = False
        self.menu.save(update_fields=["status"])

        with self.assertRaises(ValidationServiceError):
            order_service.create_staff_order_from_items(self.staff, self._data())

    def test_sold_out_menu_raises_with_name_in_message(self):
        self.menu.today_sold_out = date.today()
        self.menu.save(update_fields=["today_sold_out"])

        with self.assertRaisesMessage(ValidationServiceError, "今日已售完"):
            order_service.create_staff_order_from_items(self.staff, self._data())

        # 確認沒有誤建訂單
        self.assertEqual(Order.objects.count(), 0)


# ============================================================
#  API 層
# ============================================================


class StaffOrderCreateAPITest(TestCase):
    URL = "/api/v1/orders/staff/"

    def setUp(self):
        seed_system_options()
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type, name="炸雞", price=80, status=True
        )
        self.staff = _make_user(Identity.EMPLOYEE)
        self.customer = _make_user(Identity.CUSTOMER, phone="0911111111")

    def _payload(self, **overrides):
        payload = {
            "customer_phone": "0912345678",
            "spicy_level": "不辣",
            "extra_garlic_qty": 0,
            "extra_basil_qty": 0,
            "remark": "",
            "custom_options": [],
            "items": [{"menu_id": self.menu.pk, "qty": 1}],
        }
        payload.update(overrides)
        return payload

    def test_employee_creates_order_returns_201(self):
        resp = self.client.post(
            self.URL,
            self._payload(),
            content_type="application/json",
            **_jwt(self.staff),
        )

        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["status"], "success")
        self.assertIn("order_id", body["data"])

        order = Order.objects.get(pk=body["data"]["order_id"])
        self.assertEqual(order.status, Order.OrderStatus.ACCEPTED)

    def test_unauthenticated_returns_401_or_403(self):
        resp = self.client.post(
            self.URL, self._payload(), content_type="application/json"
        )
        self.assertIn(resp.status_code, [401, 403])

    def test_customer_identity_gets_403(self):
        resp = self.client.post(
            self.URL,
            self._payload(),
            content_type="application/json",
            **_jwt(self.customer),
        )
        self.assertIn(resp.status_code, [401, 403])

    def test_empty_phone_returns_400(self):
        resp = self.client.post(
            self.URL,
            self._payload(customer_phone=""),
            content_type="application/json",
            **_jwt(self.staff),
        )
        self.assertEqual(resp.status_code, 400)

    def test_missing_items_returns_400(self):
        resp = self.client.post(
            self.URL,
            self._payload(items=[]),
            content_type="application/json",
            **_jwt(self.staff),
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_menu_id_returns_400(self):
        resp = self.client.post(
            self.URL,
            self._payload(items=[{"menu_id": 99999, "qty": 1}]),
            content_type="application/json",
            **_jwt(self.staff),
        )
        self.assertEqual(resp.status_code, 400)

    def test_duplicate_menu_id_in_items_returns_400(self):
        resp = self.client.post(
            self.URL,
            self._payload(
                items=[
                    {"menu_id": self.menu.pk, "qty": 1},
                    {"menu_id": self.menu.pk, "qty": 2},
                ]
            ),
            content_type="application/json",
            **_jwt(self.staff),
        )
        self.assertEqual(resp.status_code, 400)
