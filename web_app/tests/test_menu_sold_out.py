"""
功能 24：今日售完測試。

涵蓋 service 層 `toggle_menu_sold_out_today`、API `MenuSoldOutTodayAPIView`
（`/api/menu/<id>/sold-out-today/`, IsEmployee）、以及結帳時售完擋單。
"""

import random
from datetime import date

from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken

from web_app.models import Identity, Menu, Type, User
from web_app.services import menu as menu_service
from web_app.services import order as order_service
from web_app.services.exceptions import NotFoundError, ValidationServiceError


def _make_user(identity=Identity.CUSTOMER, phone="0912345678"):
    uid = random.randint(100000, 999999)
    return User.objects.create(
        account=f"{phone}_{uid}",
        phone_number=phone,
        identity=identity,
        name="Test",
    )


def _auth_header(user):
    token = AccessToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


class ToggleSoldOutServiceTest(TestCase):
    def setUp(self):
        self.type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(type=self.type, name="炸雞", price=80)

    def test_toggle_on_marks_sold_out_today(self):
        result = menu_service.toggle_menu_sold_out_today(self.menu.pk)

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.today_sold_out, date.today())
        self.assertTrue(self.menu.is_sold_out_today)
        self.assertEqual(result, {"sold_out_today": True, "name": "炸雞"})

    def test_toggle_twice_clears_flag(self):
        menu_service.toggle_menu_sold_out_today(self.menu.pk)
        result = menu_service.toggle_menu_sold_out_today(self.menu.pk)

        self.menu.refresh_from_db()
        self.assertIsNone(self.menu.today_sold_out)
        self.assertFalse(self.menu.is_sold_out_today)
        self.assertEqual(result, {"sold_out_today": False, "name": "炸雞"})

    def test_missing_menu_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            menu_service.toggle_menu_sold_out_today(999999)


class SoldOutApiTest(TestCase):
    def setUp(self):
        self.type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(type=self.type, name="炸雞", price=80)
        self.staff = _make_user(Identity.EMPLOYEE)

    def _url(self, pk):
        return f"/api/menu/{pk}/sold-out-today/"

    def test_employee_can_toggle(self):
        resp = self.client.post(self._url(self.menu.pk), **_auth_header(self.staff))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")
        self.assertTrue(resp.json()["data"]["sold_out_today"])
        self.menu.refresh_from_db()
        self.assertTrue(self.menu.is_sold_out_today)

    def test_customer_forbidden(self):
        customer = _make_user(Identity.CUSTOMER, phone="0911111111")
        resp = self.client.post(self._url(self.menu.pk), **_auth_header(customer))
        self.assertIn(resp.status_code, [401, 403])

    def test_guest_forbidden(self):
        resp = self.client.post(self._url(self.menu.pk))
        self.assertIn(resp.status_code, [401, 403])

    def test_missing_menu_returns_404(self):
        resp = self.client.post(self._url(999999), **_auth_header(self.staff))
        self.assertEqual(resp.status_code, 404)


class CheckoutSoldOutGuardTest(TestCase):
    """結帳時若購物車含今日售完品項，必須擋下並提示品名。"""

    def setUp(self):
        self.type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(type=self.type, name="椒麻雞", price=100)
        self.menu.today_sold_out = date.today()
        self.menu.save(update_fields=["today_sold_out"])

    def test_create_order_rejects_sold_out_item(self):
        from unittest.mock import patch

        cart = [
            {
                "menu_id": self.menu.pk,
                "name": "椒麻雞",
                "base_price": 100,
                "options": [],
                "options_price": 0,
                "unit_price": 100,
                "quantity": 1,
                "subtotal": 100,
            }
        ]
        customer = _make_user(Identity.CUSTOMER)

        with patch("web_app.services.order.cart_service.ensure_prices_current"):
            with self.assertRaises(ValidationServiceError) as ctx:
                order_service.create_order_from_cart(
                    customer, cart, {"customer_phone": "0912345678"}
                )

        message = str(ctx.exception)
        self.assertIn("今日已售完", message)
        self.assertIn("椒麻雞", message)
