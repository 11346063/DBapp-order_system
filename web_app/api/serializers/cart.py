from rest_framework import serializers


class CartAddSerializer(serializers.Serializer):
    menu_id = serializers.IntegerField(help_text="菜單餐點 ID", default=1)
    name = serializers.CharField(help_text="餐點名稱（用於顯示購物車）", default="雞排")
    price = serializers.IntegerField(
        min_value=0,
        help_text="餐點基本價格（元，不得為負）",
        default=80,
    )
    quantity = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="加入數量（至少 1，預設 1）",
    )
    options = serializers.ListField(
        child=serializers.DictField(),
        default=list,
        help_text='選項列表，每項格式為 {"id": 1, "name": "小辣", "price": 0}',
    )


class CartAdjustSerializer(serializers.Serializer):
    menu_id = serializers.IntegerField(help_text="菜單餐點 ID", default=1)
    name = serializers.CharField(help_text="餐點名稱", default="雞排")
    price = serializers.IntegerField(
        min_value=0,
        help_text="餐點基本價格（元，不得為負）",
        default=80,
    )
    delta = serializers.IntegerField(
        help_text="數量增減值：正數加量、負數減量（歸零時自動移除品項）",
        default=1,
    )


class CartUpdateSerializer(serializers.Serializer):
    index = serializers.IntegerField(
        min_value=0,
        help_text="購物車品項索引（從 0 開始）",
        default=0,
    )
    quantity = serializers.IntegerField(
        help_text="新的數量；設為 0 或負數時移除該品項",
        default=2,
    )


class CartRemoveSerializer(serializers.Serializer):
    index = serializers.IntegerField(
        min_value=0,
        help_text="要移除的購物車品項索引（從 0 開始）",
        default=0,
    )
