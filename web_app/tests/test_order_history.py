from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from web_app.models import Identity, Menu, Order, OrderItem, Type, User


class OrderHistoryReadyNotificationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = User.objects.create_user(
            account="history_customer",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
        )
        menu_type = Type.objects.create(type_name="主餐")
        self.menu = Menu.objects.create(
            type=menu_type,
            name="香脆炸雞",
            price=80,
            status=True,
        )

    def test_ready_order_shows_pickup_notice(self):
        order = Order.objects.create(
            user=self.customer,
            status=Order.OrderStatus.READY,
            price_total=80,
            create_time=timezone.now(),
            ready_at=timezone.now(),
            ready_notified_at=timezone.now(),
            customer_phone="0912345678",
        )
        OrderItem.objects.create(
            order=order,
            menu=self.menu,
            amount=1,
            total_price=80,
        )
        self.client.login(username="history_customer", password="pass")

        response = self.client.get(reverse("web_app:order_history"))

        ready_label = "可取餐"
        pickup_notice = "餐點已完成，請留意店家電話或至櫃台取餐"
        contact_label = "聯絡電話"

        self.assertEqual(response.status_code, 200)
        self.assertIn(ready_label.encode("utf-8"), response.content)
        self.assertIn(pickup_notice.encode("utf-8"), response.content)
        self.assertIn(contact_label.encode("utf-8"), response.content)
        self.assertContains(response, "0912345678")
        self.assertContains(response, "status-ready")
        self.assertContains(response, "css/order_history.css")
        self.assertContains(response, "?v=4")
