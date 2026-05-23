import json

from django.test import Client, TestCase
from django.urls import reverse

from web_app.models import CartItem, Identity, Menu, Options, Type, User
from web_app.services import cart as cart_service
from web_app.services.exceptions import PriceChangedError


class CartDbServiceTest(TestCase):
    def setUp(self):
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type,
            name="香脆炸雞",
            price=80,
            status=True,
        )
        self.cut_option, _ = Options.objects.get_or_create(
            name="切",
            defaults={"price": 0},
        )
        self.customer = User.objects.create_user(
            account="db_cart_customer",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
        )

    def test_customer_add_item_uses_db_cart(self):
        session = {}

        result = cart_service.add_item(
            self.customer,
            session,
            {
                "menu_id": self.menu.pk,
                "name": self.menu.name,
                "price": 999,
                "quantity": 2,
                "options": [
                    {"id": self.cut_option.pk, "name": "舊切", "price": 10, "level": 1}
                ],
            },
        )

        self.assertEqual(result["cart_count"], 2)
        self.assertEqual(session, {})
        item = CartItem.objects.get(cart__user=self.customer)
        self.assertEqual(item.base_price, 80)
        self.assertEqual(item.unit_price, 80)
        self.assertEqual(item.subtotal, 160)
        self.assertEqual(item.options.get().name, "切")

    def test_validate_and_sync_prices_reports_latest_menu_price(self):
        session = {}
        cart_service.add_item(
            self.customer,
            session,
            {
                "menu_id": self.menu.pk,
                "name": self.menu.name,
                "price": self.menu.price,
                "quantity": 2,
                "options": [],
            },
        )
        self.menu.price = 85
        self.menu.save(update_fields=["price"])

        result = cart_service.validate_prices(self.customer, session)

        self.assertTrue(result["has_changes"])
        self.assertEqual(result["old_total"], 160)
        self.assertEqual(result["new_total"], 170)
        self.assertEqual(result["price_changes"][0]["old_unit_price"], 80)
        self.assertEqual(result["price_changes"][0]["new_unit_price"], 85)

        sync_result = cart_service.sync_prices(self.customer, session)

        self.assertEqual(sync_result["total"], 170)
        self.assertFalse(
            cart_service.validate_prices(self.customer, session)["has_changes"]
        )

    def test_ensure_prices_current_blocks_stale_cart(self):
        session = {}
        cart_service.add_item(
            self.customer,
            session,
            {
                "menu_id": self.menu.pk,
                "name": self.menu.name,
                "price": self.menu.price,
                "quantity": 1,
                "options": [],
            },
        )
        self.menu.price = 90
        self.menu.save(update_fields=["price"])

        with self.assertRaises(PriceChangedError):
            cart_service.ensure_prices_current(self.customer, session)

    def test_merge_session_cart_to_db_appends_and_clears_session(self):
        session = {
            "cart": [cart_service.build_cart_item(self.menu.pk, self.menu.name, 80, 1)]
        }

        result = cart_service.merge_session_cart_to_db(self.customer, session)

        self.assertEqual(result, {"merged": 1, "cart_count": 1})
        self.assertEqual(session["cart"], [])
        self.assertEqual(
            cart_service.get_cart(self.customer, session)[0]["menu_id"], self.menu.pk
        )


class CartDbApiTest(TestCase):
    def setUp(self):
        self.client = Client()
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type,
            name="香脆炸雞",
            price=80,
            status=True,
        )
        self.customer = User.objects.create_user(
            account="db_cart_api_customer",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
        )
        self.client.login(username=self.customer.account, password="pass")

    def test_v1_validate_and_sync_price_endpoints(self):
        self.client.post(
            reverse("web_app:cart_add_api"),
            data=json.dumps(
                {
                    "menu_id": self.menu.pk,
                    "name": self.menu.name,
                    "price": self.menu.price,
                    "quantity": 1,
                    "options": [],
                }
            ),
            content_type="application/json",
        )
        self.menu.price = 90
        self.menu.save(update_fields=["price"])

        validate_response = self.client.post(
            reverse("web_app:v1_cart_validate_prices_api")
        )
        self.assertEqual(validate_response.status_code, 200)
        self.assertTrue(validate_response.json()["data"]["has_changes"])

        sync_response = self.client.post(reverse("web_app:v1_cart_sync_prices_api"))
        self.assertEqual(sync_response.status_code, 200)
        self.assertEqual(sync_response.json()["data"]["total"], 90)

        detail_response = self.client.get(reverse("web_app:v1_cart_detail_api"))
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["data"]["total"], 90)


class CartCsrfApiTest(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type,
            name="香脆炸雞",
            price=80,
            status=True,
        )

    def _set_stale_session_cart(self):
        session = self.client.session
        session["cart"] = [
            cart_service.build_cart_item(
                self.menu.pk,
                self.menu.name,
                self.menu.price,
                1,
            )
        ]
        session.save()
        self.menu.price = 90
        self.menu.save(update_fields=["price"])

    def test_anonymous_sync_prices_requires_csrf_token(self):
        self._set_stale_session_cart()

        response = self.client.post(reverse("web_app:v1_cart_sync_prices_api"))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            cart_service.validate_prices(self.client.session)["has_changes"]
        )

    def test_anonymous_sync_prices_accepts_valid_csrf_token(self):
        self.client.get(reverse("web_app:home"))
        csrf_token = self.client.cookies["csrftoken"].value
        self._set_stale_session_cart()

        response = self.client.post(
            reverse("web_app:v1_cart_sync_prices_api"),
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["total"], 90)
        self.assertFalse(
            cart_service.validate_prices(self.client.session)["has_changes"]
        )
