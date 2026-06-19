"""出單機列印整合測試：接單建立列印工作、代理 API、重印。"""

import random

from django.test import TestCase, override_settings

from web_app.models import (
    Identity,
    Menu,
    Options,
    Order,
    OrderItem,
    OrderItemOption,
    PrintJob,
    Type,
    User,
)
from web_app.services import order as order_service
from web_app.services import printing as printing_service

_TOKEN = "test-print-token"


def _make_user(identity=Identity.CUSTOMER, phone="0912345678"):
    uid = random.randint(100000, 999999)
    return User.objects.create(
        account=f"{phone}_{uid}", phone_number=phone, identity=identity, name="Test"
    )


def _jwt_header(user):
    from rest_framework_simplejwt.tokens import AccessToken

    return {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(user)}"}


class EnqueueOnAcceptTest(TestCase):
    def test_accept_creates_pending_print_job(self):
        staff = _make_user(Identity.EMPLOYEE)
        order = Order.objects.create(
            status=Order.OrderStatus.SUBMITTED,
            price_total=100,
            customer_phone="0912345678",
        )

        order_service.accept_order(order.pk, staff, 20)

        jobs = PrintJob.objects.filter(order=order)
        self.assertEqual(jobs.count(), 1)
        self.assertEqual(jobs.first().status, PrintJob.Status.PENDING)


class PrintingServiceTest(TestCase):
    def test_mark_job_success_and_failure(self):
        order = Order.objects.create(
            status=Order.OrderStatus.ACCEPTED,
            price_total=100,
            customer_phone="0912345678",
        )
        job = printing_service.enqueue_print_job(order)

        self.assertTrue(printing_service.mark_job(job.pk, True))
        job.refresh_from_db()
        self.assertEqual(job.status, PrintJob.Status.PRINTED)
        self.assertIsNotNone(job.printed_at)

        job2 = printing_service.enqueue_print_job(order)
        self.assertTrue(printing_service.mark_job(job2.pk, False, "printer offline"))
        job2.refresh_from_db()
        self.assertEqual(job2.status, PrintJob.Status.FAILED)
        self.assertEqual(job2.error, "printer offline")

    def test_mark_missing_job_returns_false(self):
        self.assertFalse(printing_service.mark_job(999999, True))

    def test_pending_only_returns_pending(self):
        order = Order.objects.create(
            status=Order.OrderStatus.ACCEPTED,
            price_total=100,
            customer_phone="0912345678",
        )
        printing_service.enqueue_print_job(order)
        done = printing_service.enqueue_print_job(order)
        printing_service.mark_job(done.pk, True)

        self.assertEqual(len(printing_service.get_pending_jobs()), 1)


@override_settings(PRINT_AGENT_TOKEN=_TOKEN)
class PrintAgentApiTest(TestCase):
    def setUp(self):
        self.type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(type=self.type, name="雞排", price=80)
        self.spicy, _ = Options.objects.get_or_create(
            name="辣度", defaults={"price": 0}
        )
        self.cut, _ = Options.objects.get_or_create(name="切", defaults={"price": 0})
        self.order = Order.objects.create(
            status=Order.OrderStatus.ACCEPTED,
            price_total=160,
            customer_phone="0912345678",
            pickup_code="678",
        )
        item = OrderItem.objects.create(
            order=self.order, menu=self.menu, amount=2, total_price=160
        )
        # 品項級：切法
        OrderItemOption.objects.create(order_item=item, opt=self.cut, level=1)
        # 訂單級：辣度（大辣 = level 3）
        OrderItemOption.objects.create(order=self.order, opt=self.spicy, level=3)
        self.job = printing_service.enqueue_print_job(self.order)

    def test_pending_requires_token(self):
        resp = self.client.get("/api/print/pending/")
        self.assertIn(resp.status_code, [401, 403])

    def test_pending_rejects_wrong_token(self):
        resp = self.client.get("/api/print/pending/", HTTP_X_PRINT_TOKEN="wrong")
        self.assertIn(resp.status_code, [401, 403])

    def test_pending_returns_ticket_payload(self):
        resp = self.client.get("/api/print/pending/", HTTP_X_PRINT_TOKEN=_TOKEN)
        self.assertEqual(resp.status_code, 200)
        jobs = resp.json()["data"]["jobs"]
        self.assertEqual(len(jobs), 1)
        payload = jobs[0]
        self.assertEqual(payload["pickup_code"], "678")
        self.assertEqual(payload["order_options"], "大辣")
        self.assertEqual(payload["items"][0]["name"], "雞排")
        self.assertEqual(payload["items"][0]["amount"], 2)
        self.assertIn("切", payload["items"][0]["options"])

    def test_ack_marks_printed(self):
        resp = self.client.post(
            f"/api/print/{self.job.pk}/ack/",
            data={"success": True},
            content_type="application/json",
            HTTP_X_PRINT_TOKEN=_TOKEN,
        )
        self.assertEqual(resp.status_code, 200)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, PrintJob.Status.PRINTED)


class ReprintApiTest(TestCase):
    def setUp(self):
        self.staff = _make_user(Identity.EMPLOYEE)
        self.order = Order.objects.create(
            status=Order.OrderStatus.ACCEPTED,
            price_total=100,
            customer_phone="0912345678",
        )

    def test_employee_reprint_creates_pending_job(self):
        resp = self.client.post(
            f"/api/orders/{self.order.pk}/reprint/", **_jwt_header(self.staff)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            PrintJob.objects.filter(
                order=self.order, status=PrintJob.Status.PENDING
            ).count(),
            1,
        )

    def test_customer_cannot_reprint(self):
        customer = _make_user(Identity.CUSTOMER, phone="0911111111")
        resp = self.client.post(
            f"/api/orders/{self.order.pk}/reprint/", **_jwt_header(customer)
        )
        self.assertIn(resp.status_code, [401, 403])
