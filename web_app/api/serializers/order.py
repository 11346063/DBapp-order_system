from rest_framework import serializers


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[0, 1, 2])


class ReorderSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
