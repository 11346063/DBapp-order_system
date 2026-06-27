from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from web_app.models import (
    Identity,
    Menu,
    Options,
    Order,
    OrderItem,
    OrderItemOption,
    Type,
    User,
)
from web_app.constants import CUT_OPTION_ID
from web_app.services import order as order_service
from web_app.tests.test_helpers import seed_system_options
from web_app.services.exceptions import ValidationServiceError
from web_app.services.exceptions import EmptyCartError, StaffCustomerPhoneRequired


class OrderServiceCreateOrderTest(TestCase):
    def setUp(self):
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type,
            name="香脆炸雞",
            price=80,
            status=True,
        )
        seed_system_options()
        self.cut_option = Options.objects.get(pk=CUT_OPTION_ID)
        self.customer = User.objects.create_user(
            account="svc_customer",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
            phone_number="0912345678",
        )
        self.employee = User.objects.create_user(
            account="svc_employee",
            password="pass",
            name="員工",
            identity=Identity.EMPLOYEE,
        )

    def _cart(self):
        return [
            {
                "menu_id": self.menu.pk,
                "name": self.menu.name,
                "base_price": self.menu.price,
                "options": [
                    {"id": self.cut_option.pk, "name": "切", "price": 0, "level": 1}
                ],
                "options_price": 0,
                "unit_price": self.menu.price,
                "quantity": 2,
                "subtotal": self.menu.price * 2,
            }
        ]

    def test_create_order_from_cart_persists_items_and_options(self):
        cart = self._cart()

        order = order_service.create_order_from_cart(
            self.customer,
            cart,
            {
                "spicy_level": "中辣",
                "extra_garlic_qty": "2",
                "extra_basil_qty": "1",
                "remark": "少鹽",
            },
        )

        self.assertEqual(order.user, self.customer)
        self.assertEqual(order.price_total, 190)
        self.assertEqual(order.remark, "少鹽")
        self.assertEqual(order.customer_phone, "0912345678")

        item = OrderItem.objects.get(order=order)
        self.assertEqual(item.menu, self.menu)
        self.assertEqual(item.amount, 2)
        self.assertEqual(item.total_price, 160)

        item_option = OrderItemOption.objects.get(order_item=item)
        self.assertEqual(item_option.opt, self.cut_option)
        self.assertEqual(item_option.level, 1)

        order_options = {
            option.opt.name: option.level
            for option in OrderItemOption.objects.filter(order=order)
        }
        self.assertEqual(order_options, {"辣度": 2, "加蒜": 2, "九層塔": 1})

    def test_create_order_from_empty_cart_raises_without_creating_order(self):
        with self.assertRaises(EmptyCartError):
            order_service.create_order_from_cart(self.customer, [], {})

        self.assertEqual(Order.objects.count(), 0)

    def test_staff_order_requires_customer_phone(self):
        cart = self._cart()

        with self.assertRaises(StaffCustomerPhoneRequired):
            order_service.create_order_from_cart(self.employee, cart, {})

        self.assertEqual(Order.objects.count(), 0)

    def test_staff_order_saves_customer_phone(self):
        cart = [
            {
                "menu_id": self.menu.pk,
                "name": self.menu.name,
                "base_price": 80,
                "options": [],
                "options_price": 0,
                "unit_price": 80,
                "quantity": 2,
                "subtotal": 160,
            }
        ]

        order = order_service.create_order_from_cart(
            self.employee,
            cart,
            {"customer_phone": "0912345678"},
        )

        self.assertEqual(order.user, self.employee)
        self.assertEqual(order.customer_phone, "0912345678")


class OrderServiceStatusAndReorderTest(TestCase):
    def setUp(self):
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type,
            name="香脆炸雞",
            price=80,
            status=True,
        )
        self.customer = User.objects.create_user(
            account="reorder_cust",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
        )
        self.order = Order.objects.create(
            user=self.customer,
            status=Order.OrderStatus.SUBMITTED,
            price_total=160,
            created_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=self.order,
            menu=self.menu,
            amount=2,
            total_price=160,
        )

    def test_update_order_status_returns_refreshed_counts(self):
        self.order.status = Order.OrderStatus.READY
        self.order.save(update_fields=["status"])

        result = order_service.update_order_status(
            self.order.pk,
            Order.OrderStatus.COMPLETED,
        )

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.COMPLETED)
        self.assertEqual(result["status_counts"][Order.OrderStatus.SUBMITTED], 0)
        self.assertEqual(result["status_counts"][Order.OrderStatus.COMPLETED], 1)

    def test_update_order_status_rejects_invalid_transition(self):
        with self.assertRaises(ValidationServiceError):
            order_service.update_order_status(
                self.order.pk,
                Order.OrderStatus.COMPLETED,
            )

    def test_update_order_status_cancelled_from_submitted(self):
        result = order_service.update_order_status(
            self.order.pk,
            Order.OrderStatus.CANCELLED,
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.CANCELLED)
        self.assertIn("status_counts", result)

    def test_update_order_status_to_ready_via_accept_then_ready(self):
        self.order.status = Order.OrderStatus.ACCEPTED
        self.order.save(update_fields=["status"])

        result = order_service.mark_order_ready(self.order.pk)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.READY)
        self.assertIsNotNone(self.order.ready_at)
        self.assertIsNotNone(self.order.ready_notified_at)
        self.assertEqual(result["status_counts"][Order.OrderStatus.SUBMITTED], 0)
        self.assertEqual(result["status_counts"][Order.OrderStatus.READY], 1)

    def test_reorder_to_cart_returns_items_for_cart(self):
        result = order_service.reorder_to_cart(self.customer, self.order.pk)

        self.assertEqual(result["added"], 2)
        self.assertEqual(len(result["items"]), 1)
        item = result["items"][0]
        self.assertEqual(item["menu_id"], self.menu.pk)
        self.assertEqual(item["quantity"], 2)
        self.assertEqual(item["subtotal"], 160)


class CreateOrderFromCartDelistedItemsTest(TestCase):
    """create_order_from_cart 對購物車含下架品項應擋下並 raise NotFoundError。"""

    def setUp(self):
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type,
            name="炸雞",
            price=80,
            status=False,  # 已下架
        )
        self.customer = User.objects.create_user(
            account="delisted_cust",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
            phone_number="0912345678",
        )

    def _cart(self):
        return [
            {
                "menu_id": self.menu.pk,
                "name": "炸雞",
                "base_price": 80,
                "options": [],
                "options_price": 0,
                "unit_price": 80,
                "quantity": 1,
                "subtotal": 80,
            }
        ]

    @patch("web_app.services.order.cart_service.ensure_prices_current")
    def test_delisted_item_raises_not_found(self, _mock):
        from web_app.services.exceptions import NotFoundError

        with self.assertRaisesMessage(NotFoundError, "已下架"):
            order_service.create_order_from_cart(
                self.customer,
                self._cart(),
                {"customer_phone": "0912345678"},
            )

        self.assertEqual(Order.objects.count(), 0)


class NormalizeCheckoutDataTest(SimpleTestCase):
    """normalize_checkout_data 純函式測試（無 DB）。"""

    def test_valid_phone_returned_normalized(self):
        result = order_service.normalize_checkout_data(
            {"customer_phone": "0912345678", "remark": "少鹽"}
        )

        self.assertEqual(result["customer_phone"], "0912345678")
        self.assertEqual(result["remark"], "少鹽")

    def test_invalid_phone_raises_validation_error(self):
        from web_app.services.exceptions import ValidationServiceError

        with self.assertRaises(ValidationServiceError):
            order_service.normalize_checkout_data({"customer_phone": "not-a-phone"})

    def test_remark_truncated_to_200_characters(self):
        long_remark = "x" * 300
        result = order_service.normalize_checkout_data(
            {"customer_phone": "0912345678", "remark": long_remark}
        )

        self.assertEqual(len(result["remark"]), 200)

    def test_negative_extra_qty_clamped_to_zero(self):
        result = order_service.normalize_checkout_data(
            {
                "customer_phone": "0912345678",
                "extra_garlic_qty": -3,
                "extra_basil_qty": -1,
            }
        )

        self.assertEqual(result["extra_garlic_qty"], 0)
        self.assertEqual(result["extra_basil_qty"], 0)

    def test_missing_extras_default_to_zero(self):
        result = order_service.normalize_checkout_data({"customer_phone": "0912345678"})

        self.assertEqual(result["extra_garlic_qty"], 0)
        self.assertEqual(result["extra_basil_qty"], 0)
