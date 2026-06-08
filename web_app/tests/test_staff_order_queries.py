from django.test import Client, TestCase
from django.urls import reverse

from web_app.models import Identity, Menu, Order, OrderItem, StoreSettings, Type, User


def _make_order_with_item(menu, status=Order.OrderStatus.SUBMITTED):
    order = Order.objects.create(status=status, price_total=100)
    OrderItem.objects.create(order=order, menu=menu, amount=1, total_price=100)
    return order


class StaffOrderListQueryCountTest(TestCase):
    """P1 + T2：驗證清單/看板模式查詢數不隨訂單量 O(N) 成長。"""

    def setUp(self):
        self.client = Client()
        self.employee = User.objects.create_user(
            account="qtest_employee",
            password="pass",
            name="員工",
            identity=Identity.EMPLOYEE,
        )
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type, name="炸雞", price=80, status=True
        )
        # 確保 StoreSettings 存在，避免 get_or_create 拆成兩次查詢
        StoreSettings.objects.get_or_create(pk=1)
        self.client.login(username="qtest_employee", password="pass")

    # ------------------------------------------------------------------ list
    def test_list_view_query_count_is_constant(self):
        """清單模式：3 筆與 8 筆訂單的查詢次數相同（O(1)）。"""
        url = reverse("web_app:staff_orders")

        for _ in range(3):
            _make_order_with_item(self.menu)

        # session(1) + user(1) + status_counts(1) + get_settings(1)
        # + COUNT(1) + orders(1) + items(1) + item-opts(1) + order-opts(1)
        # + savepoint(1) + session-update(1) + release(1) = 12
        with self.assertNumQueries(12):
            self.client.get(url)

        for _ in range(5):
            _make_order_with_item(self.menu)

        with self.assertNumQueries(12):
            self.client.get(url)

    # ---------------------------------------------------------------- kanban
    def test_kanban_view_query_count_is_constant(self):
        """看板模式：每欄 2 筆與每欄 6 筆的查詢次數相同（O(1)）。"""
        url = reverse("web_app:staff_orders") + "?view=kanban"

        # 三欄各建 2 筆
        for status in (
            Order.OrderStatus.SUBMITTED,
            Order.OrderStatus.ACCEPTED,
            Order.OrderStatus.READY,
        ):
            for _ in range(2):
                _make_order_with_item(self.menu, status=status)

        # session(1) + user(1) + status_counts(1) + get_settings(1)
        # + 3 groups × 4 queries each (orders + items + item-opts + order-opts)
        # + savepoint(1) + session-update(1) + release(1) = 19
        with self.assertNumQueries(19):
            self.client.get(url)

        # 再各加 4 筆（共 6 筆/欄）——查詢數必須保持不變
        for status in (
            Order.OrderStatus.SUBMITTED,
            Order.OrderStatus.ACCEPTED,
            Order.OrderStatus.READY,
        ):
            for _ in range(4):
                _make_order_with_item(self.menu, status=status)

        with self.assertNumQueries(19):
            self.client.get(url)
