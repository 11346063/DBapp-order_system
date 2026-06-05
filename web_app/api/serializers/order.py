from rest_framework import serializers

from web_app.enums import SpicyLevel
from web_app.models import Order

_STAFF_SETTABLE = [Order.OrderStatus.COMPLETED, Order.OrderStatus.CANCELLED]
_SPICY_LABEL_CHOICES = [(s.label, s.label) for s in SpicyLevel]


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


class StaffOrderItemOptionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    level = serializers.IntegerField(default=1)
    name = serializers.CharField(required=False, default="")
    price = serializers.IntegerField(required=False, default=0, min_value=0)


class StaffOrderItemSerializer(serializers.Serializer):
    menu_id = serializers.IntegerField()
    qty = serializers.IntegerField(min_value=1)
    options = StaffOrderItemOptionSerializer(many=True, required=False, default=list)


class StaffOrderCreateSerializer(serializers.Serializer):
    customer_phone = serializers.CharField()
    spicy_level = serializers.ChoiceField(choices=_SPICY_LABEL_CHOICES, default="不辣")
    extra_garlic_qty = serializers.IntegerField(min_value=0, default=0)
    extra_basil_qty = serializers.IntegerField(min_value=0, default=0)
    custom_options = serializers.ListField(
        child=serializers.IntegerField(), default=list
    )
    remark = serializers.CharField(allow_blank=True, default="")
    items = StaffOrderItemSerializer(many=True)
