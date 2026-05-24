from django.test import TestCase
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
from web_app.services import cart as cart_service
from web_app.services import order as order_service
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
        self.cut_option, _ = Options.objects.get_or_create(
            name="切",
            defaults={"price": 0},
        )
        Options.objects.get_or_create(name="辣度", defaults={"price": 0})
        Options.objects.get_or_create(name="加蒜", defaults={"price": 10})
        Options.objects.get_or_create(name="九層塔", defaults={"price": 10})
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

    def _session_with_cart(self):
        session = {}
        cart_service.add_item(
            self.customer,
            session,
            {
                "menu_id": self.menu.pk,
                "name": self.menu.name,
                "price": self.menu.price,
                "quantity": 2,
                "options": [
                    {"id": self.cut_option.pk, "name": "切", "price": 0, "level": 1}
                ],
            },
        )
        return session

    def test_create_order_from_cart_persists_items_options_and_clears_cart(self):
        session = self._session_with_cart()

        order = order_service.create_order_from_cart(
            self.customer,
            session,
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
        self.assertEqual(cart_service.get_cart(self.customer, session), [])

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
            order_service.create_order_from_cart(self.customer, {}, {})

        self.assertEqual(Order.objects.count(), 0)

    def test_staff_order_requires_customer_phone_and_keeps_cart(self):
        session = {
            "cart": [
                cart_service.build_cart_item(
                    self.menu.pk,
                    self.menu.name,
                    self.menu.price,
                    2,
                    [{"id": self.cut_option.pk, "name": "切", "price": 0, "level": 1}],
                )
            ]
        }

        with self.assertRaises(StaffCustomerPhoneRequired):
            order_service.create_order_from_cart(self.employee, session, {})

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(len(session["cart"]), 1)

    def test_staff_order_saves_customer_phone(self):
        session = {
            "cart": [
                cart_service.build_cart_item(self.menu.pk, self.menu.name, 80, 2, [])
            ]
        }

        order = order_service.create_order_from_cart(
            self.employee,
            session,
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
        result = order_service.update_order_status(
            self.order.pk,
            Order.OrderStatus.COMPLETED,
        )

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.COMPLETED)
        self.assertEqual(result["status_counts"][Order.OrderStatus.SUBMITTED], 0)
        self.assertEqual(result["status_counts"][Order.OrderStatus.COMPLETED], 1)

    def test_update_order_status_to_ready_via_accept_then_ready(self):
        # Must be ACCEPTED before marking READY
        self.order.status = Order.OrderStatus.ACCEPTED
        self.order.save(update_fields=["status"])

        result = order_service.mark_order_ready(self.order.pk)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.READY)
        self.assertIsNotNone(self.order.ready_at)
        self.assertIsNotNone(self.order.ready_notified_at)
        self.assertEqual(result["status_counts"][Order.OrderStatus.SUBMITTED], 0)
        self.assertEqual(result["status_counts"][Order.OrderStatus.READY], 1)

    def test_reorder_to_cart_appends_menu_items(self):
        session = {}

        result = order_service.reorder_to_cart(self.customer, session, self.order.pk)

        self.assertEqual(result, {"added": 2, "cart_count": 2})
        cart = cart_service.get_cart(self.customer, session)
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0]["menu_id"], self.menu.pk)
        self.assertEqual(cart[0]["quantity"], 2)
        self.assertEqual(cart[0]["subtotal"], 160)
