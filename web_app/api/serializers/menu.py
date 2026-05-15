from rest_framework import serializers
from web_app.models import Menu, OptGroup


class MenuSerializer(serializers.ModelSerializer):
    type_name = serializers.CharField(source="type.type_name", read_only=True)
    image_url = serializers.SerializerMethodField()

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

    def get_image_url(self, obj):
        if not obj.file_path:
            return ""
        return obj.file_path.url


class MenuDetailSerializer(MenuSerializer):
    options = serializers.SerializerMethodField()

    class Meta(MenuSerializer.Meta):
        fields = MenuSerializer.Meta.fields + ["options"]

    def get_options(self, obj):
        opt_groups = OptGroup.objects.filter(menu=obj).select_related("opt")
        return [
            {"id": og.opt.id, "name": og.opt.name, "price": og.opt.price}
            for og in opt_groups
        ]
