from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from web_app.api.permissions import IsEmployee
from web_app.api.utils import api_success
from web_app.constants import SYSTEM_OPTION_IDS
from web_app.models import Options


class OptionUpdateAPIView(APIView):
    permission_classes = [IsEmployee]

    @extend_schema(
        summary="更新選項名稱或價格",
        description=(
            "PATCH 更新 Options 記錄。\n\n"
            "- **系統選項**（id 1–4）：只允許修改 `name`。\n"
            "- **自定義加料選項**：允許修改 `name`、`price`、`is_active`。"
        ),
        tags=["選項"],
        request=inline_serializer(
            name="OptionUpdateRequest",
            fields={
                "name": serializers.CharField(required=False, max_length=255),
                "price": serializers.IntegerField(required=False, min_value=0),
                "is_active": serializers.BooleanField(required=False),
            },
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="OptionUpdateResponse",
                    fields={
                        "status": serializers.CharField(default="success"),
                        "data": inline_serializer(
                            name="OptionUpdateData",
                            fields={
                                "id": serializers.IntegerField(),
                                "name": serializers.CharField(),
                                "price": serializers.IntegerField(),
                                "is_active": serializers.BooleanField(),
                            },
                        ),
                    },
                ),
            ),
        },
    )
    def patch(self, request, pk):
        opt = get_object_or_404(Options, pk=pk)
        is_system = pk in SYSTEM_OPTION_IDS
        update_fields = []

        name = request.data.get("name")
        if name is not None:
            name = str(name).strip()
            if not name:
                return Response({"status": "error", "message": "名稱不可為空"}, status=400)
            opt.name = name
            update_fields.append("name")

        if not is_system:
            price = request.data.get("price")
            if price is not None:
                try:
                    price = int(price)
                except (TypeError, ValueError):
                    return Response({"status": "error", "message": "價格必須是整數"}, status=400)
                if price < 0:
                    return Response({"status": "error", "message": "價格不可為負數"}, status=400)
                opt.price = price
                update_fields.append("price")

            is_active = request.data.get("is_active")
            if is_active is not None:
                opt.is_active = bool(is_active)
                update_fields.append("is_active")

        if update_fields:
            opt.save(update_fields=update_fields)

        return api_success({
            "id": opt.pk,
            "name": opt.name,
            "price": opt.price,
            "is_active": opt.is_active,
        })
