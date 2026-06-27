from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from .models.menu import Menu
from .models.options import Options
from .models.order import Order
from .models.type import Type
from .models.user import User
from .enums import OrderStatus


class MenuResource(resources.ModelResource):
    """菜單：可匯入（批次新增/更新）與匯出。"""

    type = fields.Field(
        column_name="分類",
        attribute="type",
        widget=ForeignKeyWidget(Type, field="name"),
    )
    name = fields.Field(column_name="名稱", attribute="name")
    price = fields.Field(column_name="價格", attribute="price")
    info = fields.Field(column_name="簡介", attribute="info")
    remark = fields.Field(column_name="備註", attribute="remark")
    status = fields.Field(column_name="上架", attribute="status")

    class Meta:
        model = Menu
        import_id_fields = ("name",)
        fields = ("id", "type", "name", "price", "info", "remark", "status")
        export_order = ("id", "type", "name", "price", "info", "remark", "status")
        skip_unchanged = True
        report_skipped = False


class OptionsResource(resources.ModelResource):
    """加料選項：可匯入與匯出。"""

    name = fields.Field(column_name="名稱", attribute="name")
    price = fields.Field(column_name="價格", attribute="price")
    is_custom_extra = fields.Field(
        column_name="自定義加料", attribute="is_custom_extra"
    )
    is_active = fields.Field(column_name="啟用", attribute="is_active")

    class Meta:
        model = Options
        import_id_fields = ("name",)
        fields = ("id", "name", "price", "is_custom_extra", "is_active")
        export_order = ("id", "name", "price", "is_custom_extra", "is_active")
        skip_unchanged = True
        report_skipped = False


class OrderResource(resources.ModelResource):
    """訂單：僅匯出（唯讀）。"""

    status_label = fields.Field(column_name="狀態")

    class Meta:
        model = Order
        fields = (
            "id",
            "pickup_code",
            "customer_phone",
            "status_label",
            "price_total",
            "remark",
            "cancel_reason",
            "created_at",
            "accepted_at",
            "ready_at",
        )
        export_order = (
            "id",
            "pickup_code",
            "customer_phone",
            "status_label",
            "price_total",
            "remark",
            "cancel_reason",
            "created_at",
            "accepted_at",
            "ready_at",
        )

    def dehydrate_status_label(self, order):
        return dict(OrderStatus.choices).get(order.status, str(order.status))

    def get_export_queryset(self, queryset, *args, **kwargs):
        return queryset.order_by("-created_at")


class UserResource(resources.ModelResource):
    """使用者：僅匯出（唯讀），排除密碼欄位。"""

    class Meta:
        model = User
        fields = (
            "id",
            "account",
            "name",
            "email",
            "phone_number",
            "identity",
            "status",
            "created_at",
        )
        export_order = (
            "id",
            "account",
            "name",
            "email",
            "phone_number",
            "identity",
            "status",
            "created_at",
        )
