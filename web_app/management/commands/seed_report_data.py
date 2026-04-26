from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from web_app.models import Identity, Menu, Order, OrderItem, Type, User


SEED_REMARK = "[seed_report_data]"


class Command(BaseCommand):
    help = "建立可重複執行的報表測試訂單資料。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="要建立近幾天的日報表資料，預設 30 天。",
        )
        parser.add_argument(
            "--months",
            type=int,
            default=12,
            help="要建立近幾個月的月報表資料，預設 12 個月。",
        )
        parser.add_argument(
            "--orders-per-day",
            type=int,
            default=2,
            help="每日完成訂單數，預設 2 筆。",
        )
        parser.add_argument(
            "--keep-existing",
            action="store_true",
            help="保留既有 seed 資料並追加新資料；預設會先刪除舊 seed。",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        days = max(options["days"], 1)
        months = max(options["months"], 1)
        orders_per_day = max(options["orders_per_day"], 1)

        deleted = 0
        if not options["keep_existing"]:
            deleted, _ = Order.objects.filter(remark__startswith=SEED_REMARK).delete()

        customer = self._get_customer()
        menus = self._get_menus()
        now = timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)

        created_orders = 0
        created_items = 0

        for day_offset in range(days):
            order_date = now - timedelta(days=day_offset)
            for index in range(orders_per_day):
                status = 1
                created_orders, created_items = self._create_order(
                    customer,
                    menus,
                    order_date + timedelta(minutes=index * 17),
                    status,
                    created_orders,
                    created_items,
                )

            if day_offset % 5 == 0:
                created_orders, created_items = self._create_order(
                    customer,
                    menus,
                    order_date + timedelta(hours=2),
                    0,
                    created_orders,
                    created_items,
                )

            if day_offset % 7 == 0:
                created_orders, created_items = self._create_order(
                    customer,
                    menus,
                    order_date + timedelta(hours=3),
                    2,
                    created_orders,
                    created_items,
                )

        for month_offset in range(1, months):
            order_date = now - timedelta(days=month_offset * 30)
            for index in range(3):
                created_orders, created_items = self._create_order(
                    customer,
                    menus,
                    order_date + timedelta(days=index, minutes=index * 23),
                    1,
                    created_orders,
                    created_items,
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed report data completed: "
                f"deleted={deleted}, orders={created_orders}, items={created_items}"
            )
        )

    def _get_customer(self):
        user, _ = User.objects.get_or_create(
            account="report_seed_customer",
            defaults={
                "name": "報表測試顧客",
                "identity": Identity.CUSTOMER,
                "email": "report-seed@example.com",
            },
        )
        if not user.has_usable_password():
            user.set_password("report-seed-pass")
            user.save(update_fields=["password"])
        return user

    def _get_menus(self):
        menu_type, _ = Type.objects.get_or_create(type_name="報表測試分類")
        defaults = [
            ("報表測試炸雞", 90),
            ("報表測試薯條", 45),
            ("報表測試飲料", 35),
        ]
        menus = []
        for name, price in defaults:
            menu, _ = Menu.objects.get_or_create(
                name=name,
                defaults={
                    "type": menu_type,
                    "price": price,
                    "info": "報表測試資料",
                    "status": True,
                },
            )
            menus.append(menu)
        return menus

    def _create_order(
        self,
        customer,
        menus,
        create_time,
        status,
        created_orders,
        created_items,
    ):
        selected = menus[created_orders % len(menus)]
        side = menus[(created_orders + 1) % len(menus)]
        amount = (created_orders % 3) + 1
        total = selected.price * amount + side.price

        order = Order.objects.create(
            user=customer,
            create_time=create_time,
            status=status,
            price_total=total,
            remark=f"{SEED_REMARK} status={status}",
        )
        OrderItem.objects.create(
            order=order,
            menu=selected,
            amount=amount,
            total_price=selected.price * amount,
        )
        OrderItem.objects.create(
            order=order,
            menu=side,
            amount=1,
            total_price=side.price,
        )
        return created_orders + 1, created_items + 2
