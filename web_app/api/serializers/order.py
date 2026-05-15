from rest_framework import serializers


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[0, 1, 2],
        help_text="訂單狀態：0=待處理、1=備餐中、2=完成",
        default=1,
    )


class ReorderSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(
        help_text="要再次訂購的歷史訂單 ID",
        default=1,
    )
