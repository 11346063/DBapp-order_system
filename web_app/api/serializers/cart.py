from rest_framework import serializers


class CartAddSerializer(serializers.Serializer):
    menu_id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.IntegerField(min_value=0)
    quantity = serializers.IntegerField(default=1, min_value=1)
    options = serializers.ListField(child=serializers.DictField(), default=list)


class CartAdjustSerializer(serializers.Serializer):
    menu_id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.IntegerField(min_value=0)
    delta = serializers.IntegerField()


class CartUpdateSerializer(serializers.Serializer):
    index = serializers.IntegerField(min_value=0)
    quantity = serializers.IntegerField()


class CartRemoveSerializer(serializers.Serializer):
    index = serializers.IntegerField(min_value=0)
