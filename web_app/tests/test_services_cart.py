from django.test import SimpleTestCase, TestCase

from web_app.models import Type, Menu
from web_app.services import cart as cart_service


class CartPureHelpersTest(SimpleTestCase):
    def _item(self, **kwargs):
        defaults = {
            "menu_id": 1,
            "name": "雞排",
            "base_price": 80,
            "options": [],
            "options_price": 0,
            "unit_price": 80,
            "quantity": 1,
            "subtotal": 80,
        }
        defaults.update(kwargs)
        return defaults

    def test_cart_count_sums_quantities(self):
        cart = [self._item(quantity=2), self._item(quantity=3)]
        self.assertEqual(cart_service.cart_count(cart), 5)

    def test_cart_total_sums_subtotals(self):
        cart = [self._item(subtotal=80), self._item(subtotal=40)]
        self.assertEqual(cart_service.cart_total(cart), 120)

    def test_summarize_cart(self):
        cart = [self._item(quantity=2, subtotal=160), self._item(quantity=1, subtotal=40)]
        result = cart_service.summarize_cart(cart)
        self.assertEqual(result["total"], 200)
        self.assertEqual(result["cart_count"], 3)

    def test_cart_count_empty(self):
        self.assertEqual(cart_service.cart_count([]), 0)

    def test_cart_total_empty(self):
        self.assertEqual(cart_service.cart_total([]), 0)


class CartValidatePricesTest(TestCase):
    def setUp(self):
        menu_type = Type.objects.create(type_name="炸雞")
        self.menu = Menu.objects.create(
            type=menu_type,
            name="香脆炸雞",
            price=80,
            status=True,
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

    def test_validate_prices_no_changes(self):
        cart = [self._item()]
        result = cart_service.validate_prices_for_cart(cart)
        self.assertFalse(result["has_changes"])
        self.assertEqual(result["price_changes"], [])

    def test_validate_prices_detects_change(self):
        cart = [self._item(price=70)]
        result = cart_service.validate_prices_for_cart(cart)
        self.assertTrue(result["has_changes"])
        self.assertEqual(len(result["price_changes"]), 1)
        change = result["price_changes"][0]
        self.assertEqual(change["old_unit_price"], 70)
        self.assertEqual(change["new_unit_price"], 80)

    def test_validate_prices_empty_cart(self):
        result = cart_service.validate_prices_for_cart([])
        self.assertFalse(result["has_changes"])
        self.assertEqual(result["old_total"], 0)

    def test_sync_prices_updates_item(self):
        cart = [self._item(price=70)]
        updated = cart_service.sync_prices_for_cart(cart)
        self.assertEqual(len(updated), 1)
        self.assertEqual(updated[0]["unit_price"], 80)
        self.assertEqual(updated[0]["subtotal"], 80)

    def test_sync_prices_empty_cart(self):
        self.assertEqual(cart_service.sync_prices_for_cart([]), [])
