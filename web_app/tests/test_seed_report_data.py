import json
from io import StringIO

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from web_app.management.commands.seed_report_data import SEED_REMARK
from web_app.models import Identity, Order, OrderItem, User


class SeedReportDataCommandTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            account="admin1",
            password="pass",
            name="管理員",
            identity=Identity.ADMIN,
        )

    def test_command_creates_reportable_orders_and_items(self):
        """指令會建立已完成訂單與訂單明細，供報表統計使用"""
        out = StringIO()
        call_command(
            "seed_report_data",
            days=3,
            months=2,
            orders_per_day=2,
            stdout=out,
        )

        seeded_orders = Order.objects.filter(remark__startswith=SEED_REMARK)
        self.assertEqual(seeded_orders.filter(status=1).count(), 9)
        self.assertGreater(seeded_orders.filter(status=0).count(), 0)
        self.assertGreater(seeded_orders.filter(status=2).count(), 0)
        self.assertEqual(OrderItem.objects.filter(order__in=seeded_orders).count(), 22)
        self.assertIn("Seed report data completed", out.getvalue())

    def test_command_is_repeatable_by_default(self):
        """重複執行預設會重建 seed 資料，不會一直追加"""
        call_command("seed_report_data", days=2, months=1, orders_per_day=1)
        first_count = Order.objects.filter(remark__startswith=SEED_REMARK).count()

        call_command("seed_report_data", days=2, months=1, orders_per_day=1)
        second_count = Order.objects.filter(remark__startswith=SEED_REMARK).count()

        self.assertEqual(first_count, second_count)

    def test_seeded_data_populates_staff_report_context(self):
        """seed 後報表頁日/月圖表資料都有內容"""
        call_command("seed_report_data", days=5, months=3, orders_per_day=1)
        self.client.login(username="admin1", password="pass")

        response = self.client.get(reverse("web_app:staff_report"))

        self.assertEqual(response.status_code, 200)
        daily_data = json.loads(response.context["daily_data"])
        monthly_data = json.loads(response.context["monthly_data"])
        self.assertGreater(len(daily_data["dates"]), 0)
        self.assertGreater(sum(daily_data["counts"]), 0)
        self.assertGreater(len(monthly_data["months"]), 0)
        self.assertGreater(sum(monthly_data["revenues"]), 0)

    def test_staff_report_uses_chart_js(self):
        """報表頁使用 Chart.js canvas，不再載入 ECharts"""
        self.client.login(username="admin1", password="pass")

        response = self.client.get(reverse("web_app:staff_report"))
        content = response.content.decode()

        self.assertContains(response, "chart.js@4")
        self.assertContains(response, '<canvas id="dailyChart"></canvas>', html=True)
        self.assertContains(response, '<canvas id="monthlyChart"></canvas>', html=True)
        self.assertNotIn("echarts", content)
