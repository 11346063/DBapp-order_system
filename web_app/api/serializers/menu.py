from drf_spectacular.utils import extend_schema_field, inline_serializer
from rest_framework import serializers

from web_app.models import Menu, OptGroup


class MenuSerializer(serializers.ModelSerializer):
    type_name = serializers.CharField(
        source="type.type_name",
        read_only=True,
        help_text="分類名稱（唯讀，由 type_id 自動帶出）",
    )
    image_url = serializers.SerializerMethodField(
        help_text="圖片完整 URL，無圖片時為空字串"
    )

    class Meta:
        model = Menu
        fields = [
            "id",
            "name",
            "price",
            "info",
            "remark",
            "type_id",
            "type_name",
            "status",
            "image_url",
        ]
        extra_kwargs = {
            "id": {"read_only": True, "help_text": "餐點唯一 ID"},
            "name": {"help_text": "餐點名稱（全系統唯一，最長 50 字）。範例：雞排"},
            "price": {"help_text": "基本售價（整數，元，不得為負）。範例：80"},
            "info": {"help_text": "餐點描述（最長 100 字，可為空）。範例：外皮酥脆、內嫩多汁"},
            "remark": {"help_text": "備註（最長 100 字，可為空）。範例：可加辣、可去骨"},
            "type_id": {"help_text": "分類 ID，對應 Type 資料表。範例：1"},
            "status": {"help_text": "上下架狀態：true=上架、false=下架"},
        }

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_image_url(self, obj):
        if not obj.file_path:
            return ""
        return obj.file_path.url


class MenuDetailSerializer(MenuSerializer):
    options = serializers.SerializerMethodField(
        help_text="此餐點可選的加購選項列表（唯讀）"
    )

    class Meta(MenuSerializer.Meta):
        fields = MenuSerializer.Meta.fields + ["options"]

    @extend_schema_field(
        serializers.ListField(
            child=inline_serializer(
                name="OptionItem",
                fields={
                    "id": serializers.IntegerField(help_text="選項 ID"),
                    "name": serializers.CharField(help_text="選項名稱，例如：小辣"),
                    "price": serializers.IntegerField(help_text="選項加價（元）"),
                },
            )
        )
    )
    def get_options(self, obj):
        opt_groups = OptGroup.objects.filter(menu=obj).select_related("opt")
        return [
            {"id": og.opt.id, "name": og.opt.name, "price": og.opt.price}
            for og in opt_groups
        ]
