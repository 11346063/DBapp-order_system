"""報表強化測試：日期區間解析、每日銷售、熱銷品項、CSV 匯出。"""

from datetime import date, datetime, timedelta

from django.test import TestCase
from django.urls import reverse

from web_app.models import Identity, Menu, Order, OrderItem, Type, User
from web_app.services import report as report_service


def _completed_order_on(d, total=100):
    o = Order.objects.create(
        status=Order.OrderStatus.COMPLETED,
        price_total=total,
        customer_phone="0912345678",
    )
    # created_at 為 auto_now_add，需以 update 繞過才能指定日期
    Order.objects.filter(pk=o.pk).update(
        created_at=datetime(d.year, d.month, d.day, 12, 0)
    )
    o.refresh_from_db()
    return o


class ParseDateRangeTest(TestCase):
    def test_defaults_to_last_30_days(self):
        today = date(2026, 6, 14)
        start, end = report_service.parse_date_range("", "", today=today)
        self.assertEqual(end, today)
        self.assertEqual(start, today - timedelta(days=29))

    def test_parses_valid_range(self):
        start, end = report_service.parse_date_range("2026-06-01", "2026-06-10")
        self.assertEqual((start, end), (date(2026, 6, 1), date(2026, 6, 10)))

    def test_invalid_value_falls_back(self):
        today = date(2026, 6, 14)
        start, end = report_service.parse_date_range("nope", "2026-06-10", today=today)
        self.assertEqual(start, today - timedelta(days=29))
        self.assertEqual(end, date(2026, 6, 10))

    def test_start_after_end_falls_back_to_default(self):
        today = date(2026, 6, 14)
        start, end = report_service.parse_date_range(
            "2026-06-20", "2026-06-10", today=today
        )
        self.assertEqual(end, today)
        self.assertEqual(start, today - timedelta(days=29))


class DailySalesTest(TestCase):
    def setUp(self):
        self.type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(type=self.type, name="雞排", price=80)

    def test_aggregates_completed_orders_in_range(self):
        _completed_order_on(date(2026, 6, 10), total=100)
        _completed_order_on(date(2026, 6, 10), total=50)
        _completed_order_on(date(2026, 6, 1), total=999)  # 區間外
        out = Order.objects.create(
            status=Order.OrderStatus.SUBMITTED,
            price_total=70,
            customer_phone="0912345678",
        )
        Order.objects.filter(pk=out.pk).update(created_at=datetime(2026, 6, 10, 12, 0))

        rows = report_service.daily_sales(date(2026, 6, 5), date(2026, 6, 15))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["count"], 2)
        self.assertEqual(rows[0]["revenue"], 150)


class TopSellingItemsTest(TestCase):
    def setUp(self):
        self.type = Type.objects.create(type_name="主餐")
        self.a = Menu.objects.create(type=self.type, name="雞排", price=80)
        self.b = Menu.objects.create(type=self.type, name="雞塊", price=60)

    def test_ranks_by_quantity(self):
        order = _completed_order_on(date(2026, 6, 10))
        OrderItem.objects.create(order=order, menu=self.a, amount=2, total_price=160)
        OrderItem.objects.create(order=order, menu=self.b, amount=5, total_price=300)

        rows = report_service.top_selling_items(date(2026, 6, 1), date(2026, 6, 30))

        self.assertEqual(rows[0]["menu__name"], "雞塊")
        self.assertEqual(rows[0]["qty"], 5)
        self.assertEqual(rows[1]["menu__name"], "雞排")

    def test_excludes_non_completed_and_out_of_range(self):
        pending = Order.objects.create(
            status=Order.OrderStatus.SUBMITTED,
            price_total=80,
            customer_phone="0912345678",
        )
        Order.objects.filter(pk=pending.pk).update(
            created_at=datetime(2026, 6, 10, 12, 0)
        )
        OrderItem.objects.create(order=pending, menu=self.a, amount=9, total_price=720)

        rows = report_service.top_selling_items(date(2026, 6, 1), date(2026, 6, 30))

        self.assertEqual(rows, [])


class ReportExportViewTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            account="admin_r", password="pass", name="A", identity=Identity.ADMIN
        )
        self.customer = User.objects.create_user(
            account="cust_r", password="pass", name="C", identity=Identity.CUSTOMER
        )
        Type.objects.create(type_name="主餐")

    def test_admin_downloads_csv(self):
        _completed_order_on(date(2026, 6, 10), total=120)
        self.client.force_login(self.admin)

        resp = self.client.get(
            reverse("web_app:staff_report_export") + "?start=2026-06-01&end=2026-06-30"
        )

        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])
        self.assertIn("attachment", resp["Content-Disposition"])
        content = resp.content.decode("utf-8-sig")
        self.assertIn("日期", content)
        self.assertIn("2026-06-10", content)
        self.assertIn("120", content)

    def test_customer_cannot_export(self):
        self.client.force_login(self.customer)
        resp = self.client.get(reverse("web_app:staff_report_export"))
        self.assertIn(resp.status_code, [302, 403])
