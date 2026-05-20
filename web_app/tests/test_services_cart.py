from django.test import SimpleTestCase

from web_app.services import cart as cart_service


class CartServiceTest(SimpleTestCase):
    def test_add_item_stores_cart_payload_and_count(self):
        session = {}

        result = cart_service.add_item(
            session,
            {
                "menu_id": 1,
                "name": "雞排",
                "price": 80,
                "quantity": 2,
                "options": [{"id": 3, "name": "切", "price": 5}],
            },
        )

        self.assertEqual(result, {"cart_count": 2})
        self.assertEqual(
            session["cart"],
            [
                {
                    "menu_id": 1,
                    "name": "雞排",
                    "base_price": 80,
                    "options": [{"id": 3, "name": "切", "price": 5}],
                    "options_price": 5,
                    "unit_price": 85,
                    "quantity": 2,
                    "subtotal": 170,
                }
            ],
        )

    def test_adjust_item_creates_updates_and_removes_optionless_item(self):
        session = {}

        added = cart_service.adjust_item(
            session,
            {"menu_id": 1, "name": "雞排", "price": 80, "delta": 2},
        )
        reduced = cart_service.adjust_item(
            session,
            {"menu_id": 1, "name": "雞排", "price": 80, "delta": -1},
        )
        removed = cart_service.adjust_item(
            session,
            {"menu_id": 1, "name": "雞排", "price": 80, "delta": -1},
        )

        self.assertEqual(added, {"cart_count": 2, "item_quantity": 2})
        self.assertEqual(reduced, {"cart_count": 1, "item_quantity": 1})
        self.assertEqual(removed, {"cart_count": 0, "item_quantity": 0})
        self.assertEqual(session["cart"], [])

    def test_adjust_item_ignores_same_menu_item_with_options(self):
        session = {
            "cart": [
                cart_service.build_cart_item(
                    1,
                    "雞排",
                    80,
                    1,
                    [{"id": 3, "name": "切", "price": 0}],
                )
            ]
        }

        result = cart_service.adjust_item(
            session,
            {"menu_id": 1, "name": "雞排", "price": 80, "delta": 1},
        )

        self.assertEqual(result, {"cart_count": 2, "item_quantity": 1})
        self.assertEqual(len(session["cart"]), 2)
        self.assertEqual(session["cart"][0]["options"][0]["name"], "切")
        self.assertEqual(session["cart"][1]["options"], [])

    def test_update_item_quantity_silently_ignores_out_of_range_index(self):
        session = {"cart": [cart_service.build_cart_item(1, "雞排", 80, 1)]}

        result = cart_service.update_item_quantity(session, 99, 3)

        self.assertEqual(result, {"total": 80, "cart_count": 1})
        self.assertEqual(session["cart"][0]["quantity"], 1)

    def test_update_item_quantity_removes_when_quantity_is_zero(self):
        session = {"cart": [cart_service.build_cart_item(1, "雞排", 80, 1)]}

        result = cart_service.update_item_quantity(session, 0, 0)

        self.assertEqual(result, {"total": 0, "cart_count": 0})
        self.assertEqual(session["cart"], [])

    def test_remove_last_item_by_menu_removes_latest_matching_row(self):
        session = {
            "cart": [
                cart_service.build_cart_item(1, "雞排", 80, 2),
                cart_service.build_cart_item(2, "甜不辣", 40, 1),
                cart_service.build_cart_item(1, "雞排", 80, 1),
            ]
        }

        result = cart_service.remove_last_item_by_menu(session, 1)

        self.assertEqual(result, {"cart_count": 3, "item_quantity": 2})
        self.assertEqual(len(session["cart"]), 2)
        self.assertEqual(session["cart"][0]["menu_id"], 1)
        self.assertEqual(session["cart"][1]["menu_id"], 2)
