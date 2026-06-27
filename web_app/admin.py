import csv

from django.contrib import admin
from django.db.models import Count
from django.http import HttpResponse

from .enums import OrderStatus
from .models.menu import Menu
from .models.opt_group import OptGroup
from .models.options import Options
from .models.order import Order
from .models.order_item import OrderItem
from .models.order_item_options import OrderItemOption
from .models.print_job import PrintJob
from .models.store_settings import StoreSettings
from .models.type import Type
from .models.user import User


# ── Inlines ────────────────────────────────────────────────────────────────────


class OrderItemOptionInline(admin.TabularInline):
    model = OrderItemOption
    fk_name = "order"
    extra = 0
    readonly_fields = ("opt", "level")
    can_delete = False
    verbose_name = "訂單選項（辣度／加料）"
    verbose_name_plural = "訂單選項（辣度／加料）"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("menu", "amount", "total_price", "is_deleted")
    can_delete = False
    verbose_name = "訂購品項"
    verbose_name_plural = "訂購品項"

    def get_queryset(self, request):
        # 顯示含軟刪除的所有品項
        return OrderItem.all_objects.all()


# ── Actions ────────────────────────────────────────────────────────────────────


@admin.action(description="將選取訂單標為「已完成」")
def mark_completed(modeladmin, request, queryset):
    updated = queryset.update(status=OrderStatus.COMPLETED)
    modeladmin.message_user(request, f"已將 {updated} 筆訂單標為「已完成」。")


@admin.action(description="將選取訂單標為「已取消」")
def mark_cancelled(modeladmin, request, queryset):
    updated = queryset.update(status=OrderStatus.CANCELLED)
    modeladmin.message_user(request, f"已將 {updated} 筆訂單標為「已取消」。")


@admin.action(description="匯出選取訂單為 CSV")
def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(
        ["訂單ID", "取餐號碼", "聯絡電話", "狀態", "總金額", "建立時間", "取消原因"]
    )
    status_map = dict(OrderStatus.choices)
    for order in queryset.order_by("-created_at"):
        writer.writerow(
            [
                order.id,
                order.pickup_code,
                order.customer_phone,
                status_map.get(order.status, order.status),
                order.price_total,
                order.created_at.strftime("%Y-%m-%d %H:%M"),
                order.cancel_reason,
            ]
        )
    return response


# ── ModelAdmin ─────────────────────────────────────────────────────────────────

_STATUS_LABEL = {
    OrderStatus.SUBMITTED: "等待接單",
    OrderStatus.ACCEPTED: "備餐中",
    OrderStatus.READY: "可取餐",
    OrderStatus.COMPLETED: "已完成",
    OrderStatus.CANCELLED: "已取消",
}


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "pickup_code",
        "customer_phone",
        "status_badge",
        "price_total_display",
        "item_count",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("id", "pickup_code", "customer_phone")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    inlines = [OrderItemInline, OrderItemOptionInline]
    actions = [mark_completed, mark_cancelled, export_as_csv]
    readonly_fields = (
        "id",
        "created_at",
        "accepted_at",
        "ready_at",
        "ready_notified_at",
        "price_total",
    )
    fieldsets = (
        (
            "訂單識別",
            {
                "fields": ("id", "pickup_code", "status", "customer_phone"),
            },
        ),
        (
            "金額與備註",
            {
                "fields": ("price_total", "remark", "cancel_reason"),
            },
        ),
        (
            "時間紀錄",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "accepted_at",
                    "estimated_wait_minutes",
                    "ready_at",
                    "ready_notified_at",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_item_count=Count("orderitem"))

    @admin.display(description="狀態", ordering="status")
    def status_badge(self, obj):
        return _STATUS_LABEL.get(obj.status, str(obj.status))

    @admin.display(description="總金額", ordering="price_total")
    def price_total_display(self, obj):
        return f"NT${obj.price_total}"

    @admin.display(description="品項數", ordering="_item_count")
    def item_count(self, obj):
        return obj._item_count


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "price", "status", "remark")
    list_editable = ("price",)
    list_filter = ("type", "status")
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "account",
        "phone_number",
        "identity",
        "status",
        "updated_at",
    )
    list_filter = ("status", "identity")
    search_fields = ("name", "account", "phone_number")
    exclude = ("password",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "status", "created_at", "printed_at", "error")
    list_filter = ("status",)
    ordering = ("-created_at",)
    readonly_fields = ("order", "created_at", "printed_at", "error")


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "business_hours_enabled", "open_time", "close_time")

    def has_add_permission(self, request):
        # 僅允許一筆設定記錄
        return not StoreSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ── 基礎模型（無需客製化）──────────────────────────────────────────────────────

admin.site.register(Type)
admin.site.register(Options)
admin.site.register(OptGroup)
