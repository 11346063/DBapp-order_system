from rest_framework import serializers
from web_app.models import Order

_STAFF_SETTABLE = [Order.OrderStatus.COMPLETED, Order.OrderStatus.CANCELLED]


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[(s.value, s.label) for s in _STAFF_SETTABLE],
        help_text="訂單狀態：3=已完成、4=已取消",
        default=Order.OrderStatus.COMPLETED,
    )


class AcceptOrderSerializer(serializers.Serializer):
    estimated_wait_minutes = serializers.IntegerField(
        min_value=1,
        max_value=180,
        help_text="預估等待時間（分鐘），1–180",
    )


class ReorderSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(
        help_text="要再次訂購的歷史訂單 ID",
        default=1,
    )
