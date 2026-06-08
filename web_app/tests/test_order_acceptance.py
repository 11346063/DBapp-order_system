"""
Tests for Phase 11 item 17+18: order acceptance flow.
"""

from unittest.mock import patch

from django.test import TestCase

from web_app.models import Identity, Order, User
from web_app.services import order as order_service
from web_app.services.exceptions import NotFoundError, ValidationServiceError


def _make_user(identity=Identity.CUSTOMER, phone="0912345678"):
    import random

    uid = random.randint(100000, 999999)
    return User.objects.create(
        account=f"{phone}_{uid}",
        phone_number=phone,
        identity=identity,
        name="Test",
    )


def _make_order(status=Order.OrderStatus.SUBMITTED):
    return Order.objects.create(
        status=status,
        price_total=100,
        customer_phone="0912345678",
    )


class OrderStatusChoicesTest(TestCase):
    def test_submitted_is_zero(self):
        self.assertEqual(Order.OrderStatus.SUBMITTED, 0)

    def test_accepted_is_one(self):
        self.assertEqual(Order.OrderStatus.ACCEPTED, 1)

    def test_ready_is_two(self):
        self.assertEqual(Order.OrderStatus.READY, 2)

    def test_completed_is_three(self):
        self.assertEqual(Order.OrderStatus.COMPLETED, 3)

    def test_cancelled_is_four(self):
        self.assertEqual(Order.OrderStatus.CANCELLED, 4)


class AcceptOrderServiceTest(TestCase):
    def setUp(self):
        self.staff = _make_user(Identity.EMPLOYEE)

    def test_accept_submitted_order(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)
        result = order_service.accept_order(order.pk, self.staff, 20)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.ACCEPTED)
        self.assertEqual(order.estimated_wait_minutes, 20)
        self.assertEqual(order.accepted_by, self.staff)
        self.assertIsNotNone(order.accepted_at)
        self.assertTrue(order.pickup_code)
        self.assertEqual(result["estimated_wait_minutes"], 20)

    def test_accept_sets_pickup_code_from_phone(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)
        order_service.accept_order(order.pk, self.staff, 15)
        order.refresh_from_db()
        # 電話 0912345678 → 後 3 碼 678（今日第一筆，不衝突）
        self.assertEqual(order.pickup_code, "678")

    def test_accept_pickup_code_extends_on_collision(self):
        # 先建一筆已占用 678 的今日訂單
        existing = _make_order(Order.OrderStatus.ACCEPTED)
        existing.pickup_code = "678"
        existing.save(update_fields=["pickup_code"])

        order = _make_order(Order.OrderStatus.SUBMITTED)
        order_service.accept_order(order.pk, self.staff, 15)
        order.refresh_from_db()
        # 678 被占用 → 往前一碼變 5678
        self.assertEqual(order.pickup_code, "5678")

    def test_accept_non_submitted_raises(self):
        order = _make_order(Order.OrderStatus.ACCEPTED)
        with self.assertRaises(ValidationServiceError):
            order_service.accept_order(order.pk, self.staff, 20)

    def test_accept_cancelled_raises(self):
        order = _make_order(Order.OrderStatus.CANCELLED)
        with self.assertRaises(ValidationServiceError):
            order_service.accept_order(order.pk, self.staff, 20)

    def test_accept_invalid_wait_time_zero(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)
        with self.assertRaises(ValidationServiceError):
            order_service.accept_order(order.pk, self.staff, 0)

    def test_accept_invalid_wait_time_over_limit(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)
        with self.assertRaises(ValidationServiceError):
            order_service.accept_order(order.pk, self.staff, 181)

    def test_accept_wait_time_boundary_one(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)
        result = order_service.accept_order(order.pk, self.staff, 1)
        self.assertEqual(result["estimated_wait_minutes"], 1)

    def test_accept_wait_time_boundary_180(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)
        result = order_service.accept_order(order.pk, self.staff, 180)
        self.assertEqual(result["estimated_wait_minutes"], 180)

    def test_accept_not_found_raises(self):
        with self.assertRaises(NotFoundError):
            order_service.accept_order(99999, self.staff, 20)

    def test_accept_returns_status_counts(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)
        result = order_service.accept_order(order.pk, self.staff, 20)
        self.assertIn("status_counts", result)
        self.assertIn(Order.OrderStatus.SUBMITTED, result["status_counts"])
        self.assertIn(Order.OrderStatus.ACCEPTED, result["status_counts"])


class MarkOrderReadyServiceTest(TestCase):
    def test_mark_accepted_order_ready(self):
        order = _make_order(Order.OrderStatus.ACCEPTED)
        order_service.mark_order_ready(order.pk)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.READY)
        self.assertIsNotNone(order.ready_at)
        self.assertIsNotNone(order.ready_notified_at)

    def test_mark_submitted_order_ready_raises(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)
        with self.assertRaises(ValidationServiceError):
            order_service.mark_order_ready(order.pk)

    def test_mark_ready_not_found_raises(self):
        with self.assertRaises(NotFoundError):
            order_service.mark_order_ready(99999)


class OrderStatusCountsTest(TestCase):
    def test_counts_include_all_five_statuses(self):
        counts = order_service.order_status_counts()
        for status in Order.OrderStatus:
            self.assertIn(status, counts)

    def test_submitted_count_increments(self):
        before = order_service.order_status_counts()[Order.OrderStatus.SUBMITTED]
        _make_order(Order.OrderStatus.SUBMITTED)
        after = order_service.order_status_counts()[Order.OrderStatus.SUBMITTED]
        self.assertEqual(after, before + 1)


class OrderAcceptAPITest(TestCase):
    def setUp(self):
        self.staff = _make_user(Identity.EMPLOYEE)
        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken.for_user(self.staff)
        self.auth_header = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_accept_api_success(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)
        resp = self.client.post(
            f"/api/orders/{order.pk}/accept/",
            {"estimated_wait_minutes": 25},
            content_type="application/json",
            **self.auth_header,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")
        self.assertEqual(resp.json()["data"]["estimated_wait_minutes"], 25)

    def test_accept_api_requires_auth(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)
        resp = self.client.post(
            f"/api/orders/{order.pk}/accept/",
            {"estimated_wait_minutes": 20},
            content_type="application/json",
        )
        self.assertIn(resp.status_code, [401, 403])

    def test_accept_api_invalid_wait_time(self):
        order = _make_order(Order.OrderStatus.SUBMITTED)
        resp = self.client.post(
            f"/api/orders/{order.pk}/accept/",
            {"estimated_wait_minutes": 0},
            content_type="application/json",
            **self.auth_header,
        )
        self.assertEqual(resp.status_code, 400)

    def test_accept_api_already_accepted(self):
        order = _make_order(Order.OrderStatus.ACCEPTED)
        resp = self.client.post(
            f"/api/orders/{order.pk}/accept/",
            {"estimated_wait_minutes": 20},
            content_type="application/json",
            **self.auth_header,
        )
        self.assertEqual(resp.status_code, 400)

    def test_accept_api_not_found(self):
        resp = self.client.post(
            "/api/orders/99999/accept/",
            {"estimated_wait_minutes": 20},
            content_type="application/json",
            **self.auth_header,
        )
        self.assertEqual(resp.status_code, 404)


class CreateOrderInitialStatusTest(TestCase):
    """Verify new orders start as SUBMITTED; staff orders start as ACCEPTED."""

    def _patch_cart(self, cart):
        return patch.multiple(
            "web_app.services.order.cart_service",
            ensure_prices_current=lambda *a, **k: None,
            get_cart=lambda *a, **k: cart,
            cart_total=lambda *a, **k: 100,
            clear_cart=lambda *a, **k: None,
        )

    def test_customer_order_starts_submitted(self):
        from web_app.models import Menu, Type

        menu_type = Type.objects.create(type_name="主餐")
        menu = Menu.objects.create(type=menu_type, name="測試品項", price=100)
        cart = [{"menu_id": menu.pk, "quantity": 1, "subtotal": 100, "options": []}]

        customer = _make_user(Identity.CUSTOMER)
        session = {}

        with self._patch_cart(cart):
            order = order_service.create_order_from_cart(
                customer, session, {"customer_phone": "0912345678"}
            )

        self.assertEqual(order.status, Order.OrderStatus.SUBMITTED)

    def test_staff_order_starts_accepted(self):
        from web_app.models import Menu, Type

        menu_type = Type.objects.create(type_name="主餐")
        menu = Menu.objects.create(type=menu_type, name="測試品項2", price=100)
        cart = [{"menu_id": menu.pk, "quantity": 1, "subtotal": 100, "options": []}]

        staff = _make_user(Identity.EMPLOYEE, phone="0922222222")
        session = {}

        with self._patch_cart(cart):
            order = order_service.create_order_from_cart(
                staff, session, {"customer_phone": "0933333333"}
            )

        self.assertEqual(order.status, Order.OrderStatus.ACCEPTED)
