from rest_framework import serializers
from web_app.models import Order


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=Order.OrderStatus.choices,
        help_text="訂單狀態：0=等待中、1=已完成、2=已取消",
        default=Order.OrderStatus.COMPLETED,
    )


class ReorderSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(
        help_text="要再次訂購的歷史訂單 ID",
        default=1,
    )
