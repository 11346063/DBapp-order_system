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
        Order.objects.create(status=0, price_total=100, created_at=now)  # SUBMITTED
        Order.objects.create(status=3, price_total=200, created_at=now)  # COMPLETED
        Order.objects.create(status=4, price_total=300, created_at=now)  # CANCELLED
        Order.objects.create(status=2, price_total=350, created_at=now)  # READY
        Order.objects.create(
            user=self.employee,
            status=0,
            price_total=400,
            created_at=now,
            customer_phone="0912345678",
        )
        Order.objects.create(
            status=0,
            price_total=500,
            created_at=now,
            customer_phone="0922333444",
        )

    def test_staff_order_tabs_use_right_aligned_badge_structure(self):
        self.client.login(username="staff_nav_employee", password="pass")

        response = self.client.get(reverse("web_app:staff_orders"))

        self.assertContains(response, "staff-nav-label", count=10)
        self.assertContains(response, "staff-status-badge", count=10)
        self.assertContains(response, 'data-status-count="0"', count=2)
        self.assertContains(response, 'data-status-count="1"', count=2)
        self.assertContains(response, 'data-status-count="2"', count=2)
        self.assertContains(response, 'data-status-count="3"', count=2)
        self.assertContains(response, 'data-status-count="4"', count=2)
        self.assertContains(response, "等待接單")
        self.assertContains(response, "備餐中")
        self.assertContains(response, "可取餐")
        self.assertContains(response, "已完成")
        self.assertContains(response, "已取消")
        self.assertContains(response, "css/staff.css")
        self.assertContains(response, "?v=3")
        self.assertContains(response, "js/staff.js")
        self.assertContains(response, "?v=9")
        self.assertContains(response, 'id="orderStatusConfirmModal"')
        self.assertContains(response, "確認更新訂單")
        self.assertContains(response, 'id="orderAcceptModal"')
        self.assertContains(response, "同意接單")

    def test_staff_report_keeps_badge_structure_and_no_status_active(self):
        self.client.login(username="staff_nav_admin", password="pass")

        response = self.client.get(reverse("web_app:staff_report"))

        self.assertIsNone(response.context["current_status"])
        self.assertContains(response, "staff-status-badge", count=10)
        self.assertContains(response, reverse("web_app:staff_report"))
        self.assertContains(response, "報表")

    def test_status_update_to_completed_returns_refreshed_counts(self):
        self.client.login(username="staff_nav_employee", password="pass")
        order = Order.objects.filter(status=0).first()
        # Must be READY before COMPLETED (state machine requires ACCEPTED or READY → COMPLETED)
        order.status = Order.OrderStatus.READY
        order.save(update_fields=["status"])

        response = self.client.post(
            reverse("web_app:api_order_status", kwargs={"pk": order.pk}),
            data=json.dumps({"status": 3}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["status_counts"]["0"], 2)
        self.assertEqual(data["data"]["status_counts"]["3"], 2)

    def test_status_update_rejects_invalid_status(self):
        self.client.login(username="staff_nav_employee", password="pass")
        order = Order.objects.filter(status=0).first()

        response = self.client.post(
            reverse("web_app:api_order_status", kwargs={"pk": order.pk}),
            data=json.dumps({"status": 1}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_ready_endpoint_requires_accepted_state(self):
        self.client.login(username="staff_nav_employee", password="pass")
        order = Order.objects.filter(status=0).first()

        response = self.client.post(
            reverse("web_app:api_order_ready", kwargs={"pk": order.pk}),
        )

        self.assertEqual(response.status_code, 400)

    def test_ready_endpoint_records_notification_time(self):
        self.client.login(username="staff_nav_employee", password="pass")
        order = Order.objects.filter(status=0).first()
        order.status = Order.OrderStatus.ACCEPTED
        order.save(update_fields=["status"])

        response = self.client.post(
            reverse("web_app:api_order_ready", kwargs={"pk": order.pk}),
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.READY)
        self.assertIsNotNone(order.ready_at)
        self.assertIsNotNone(order.ready_notified_at)
