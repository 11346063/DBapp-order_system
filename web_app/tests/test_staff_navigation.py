from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
import json

from web_app.models import Identity, Order, User


class StaffNavigationBadgeTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            account="staff_nav_admin",
            password="pass",
            name="管理員",
            identity=Identity.ADMIN,
        )
        self.employee = User.objects.create_user(
            account="staff_nav_employee",
            password="pass",
            name="員工",
            identity=Identity.EMPLOYEE,
        )
        now = timezone.now()
        Order.objects.create(status=0, price_total=100, create_time=now)
        Order.objects.create(status=1, price_total=200, create_time=now)
        Order.objects.create(status=2, price_total=300, create_time=now)
        Order.objects.create(
            user=self.employee,
            status=0,
            price_total=400,
            create_time=now,
            customer_phone="0912345678",
        )

    def test_staff_order_tabs_use_right_aligned_badge_structure(self):
        self.client.login(username="staff_nav_employee", password="pass")

        response = self.client.get(reverse("web_app:staff_orders"))

        self.assertContains(response, "staff-nav-label", count=6)
        self.assertContains(response, "staff-status-badge", count=6)
        self.assertContains(response, 'data-status-count="0"', count=2)
        self.assertContains(response, 'data-status-count="1"', count=2)
        self.assertContains(response, 'data-status-count="2"', count=2)
        self.assertContains(response, "等待中")
        self.assertContains(response, "已完成")
        self.assertContains(response, "已取消")
        self.assertContains(response, "css/staff.css")
        self.assertContains(response, "?v=2")
        self.assertContains(response, "js/staff.js")
        self.assertContains(response, "?v=4")
        self.assertContains(response, 'id="orderStatusConfirmModal"')
        self.assertContains(response, "確認更新訂單")
        self.assertContains(response, "電話客人")
        self.assertContains(response, "0912345678")

    def test_staff_report_keeps_badge_structure_and_no_status_active(self):
        self.client.login(username="staff_nav_admin", password="pass")

        response = self.client.get(reverse("web_app:staff_report"))

        self.assertIsNone(response.context["current_status"])
        self.assertContains(response, "staff-status-badge", count=6)
        self.assertContains(response, reverse("web_app:staff_report"))
        self.assertContains(response, "報表")

    def test_status_update_returns_refreshed_counts(self):
        self.client.login(username="staff_nav_employee", password="pass")
        order = Order.objects.filter(status=0).first()

        response = self.client.post(
            reverse("web_app:staff_order_status", kwargs={"pk": order.pk}),
            data=json.dumps({"status": 1}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["status_counts"]["0"], 1)
        self.assertEqual(data["status_counts"]["1"], 2)
        self.assertEqual(data["status_counts"]["2"], 1)
