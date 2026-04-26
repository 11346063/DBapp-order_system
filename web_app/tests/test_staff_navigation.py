from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

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

    def test_staff_order_tabs_use_right_aligned_badge_structure(self):
        self.client.login(username="staff_nav_employee", password="pass")

        response = self.client.get(reverse("web_app:staff_orders"))

        self.assertContains(response, "staff-nav-label", count=6)
        self.assertContains(response, "staff-status-badge", count=6)
        self.assertContains(response, "等待中")
        self.assertContains(response, "已完成")
        self.assertContains(response, "已取消")

    def test_staff_report_keeps_badge_structure_and_no_status_active(self):
        self.client.login(username="staff_nav_admin", password="pass")

        response = self.client.get(reverse("web_app:staff_report"))

        self.assertIsNone(response.context["current_status"])
        self.assertContains(response, "staff-status-badge", count=6)
        self.assertContains(response, reverse("web_app:staff_report"))
        self.assertContains(response, "報表")
