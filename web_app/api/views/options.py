from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from web_app.api.permissions import IsEmployee
from web_app.api.utils import api_success, parse_bool_param
from web_app.constants import SYSTEM_OPTION_IDS
from web_app.models import Options


_OptionListItem = inline_serializer(
    name="OptionListItem",
    fields={
        "id": serializers.IntegerField(help_text="選項 ID"),
        "name": serializers.CharField(help_text="選項名稱"),
        "price": serializers.IntegerField(help_text="加價金額（元）"),
        "is_custom_extra": serializers.BooleanField(
            help_text="true = 自定義加料選項；false = 系統選項（辣度/切法等）"
        ),
        "is_active": serializers.BooleanField(help_text="是否啟用"),
    },
)

_OptionsListSuccessResponse = inline_serializer(
    name="OptionsListSuccessResponse",
    fields={
        "status": serializers.CharField(default="success"),
        "message": serializers.CharField(default="操作成功"),
        "data": inline_serializer(
            name="OptionsListData",
            fields={
                "items": serializers.ListField(child=_OptionListItem),
                "total": serializers.IntegerField(help_text="符合條件的選項總筆數"),
            },
        ),
    },
)


class OptionsListAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="取得加料選項列表",
        description=(
            "回傳所有符合篩選條件的選項（辣度、切法、自定義加料等）。\n\n"
            "- **`is_custom_extra=true`**：僅回傳自定義加料選項（顧客結帳時可勾選）。\n"
            "- **`is_custom_extra=false`**：僅回傳系統選項（辣度、加蒜、九層塔、切法）。\n"
            "- **`is_active`**：過濾啟用狀態，預設不限制（全回傳）。\n"
            "- 不帶任何參數時回傳全部選項。"
        ),
        tags=["選項"],
        parameters=[
            OpenApiParameter(
                name="is_custom_extra",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="過濾選項類型：true=自定義加料，false=系統選項（選填）",
                required=False,
            ),
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="過濾啟用狀態：true=啟用中，false=已停用（選填，預設不限制）",
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=_OptionsListSuccessResponse,
                description="成功取得選項列表",
                examples=[
                    OpenApiExample(
                        "自定義加料（啟用中）",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {
                                "items": [
                                    {
                                        "id": 5,
                                        "name": "梅粉",
                                        "price": 0,
                                        "is_custom_extra": True,
                                        "is_active": True,
                                    }
                                ],
                                "total": 1,
                            },
                        },
                    ),
                    OpenApiExample(
                        "系統選項",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {
                                "items": [
                                    {
                                        "id": 1,
                                        "name": "辣度",
                                        "price": 0,
                                        "is_custom_extra": False,
                                        "is_active": True,
                                    },
                                    {
                                        "id": 2,
                                        "name": "加蒜",
                                        "price": 10,
                                        "is_custom_extra": False,
                                        "is_active": True,
                                    },
                                ],
                                "total": 2,
                            },
                        },
                    ),
                ],
            ),
        },
    )
    def get(self, request):
        qs = Options.objects.all()

        is_custom_extra = request.query_params.get("is_custom_extra")
        if is_custom_extra is not None:
            qs = qs.filter(is_custom_extra=parse_bool_param(is_custom_extra))

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=parse_bool_param(is_active))

        data = [
            {
                "id": opt.pk,
                "name": opt.name,
                "price": opt.price,
                "is_custom_extra": opt.is_custom_extra,
                "is_active": opt.is_active,
            }
            for opt in qs.order_by("id")
        ]
        return api_success({"items": data, "total": len(data)})


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
                return Response(
                    {"status": "error", "message": "名稱不可為空"}, status=400
                )
            opt.name = name
            update_fields.append("name")

        if not is_system:
            price = request.data.get("price")
            if price is not None:
                try:
                    price = int(price)
                except (TypeError, ValueError):
                    return Response(
                        {"status": "error", "message": "價格必須是整數"}, status=400
                    )
                if price < 0:
                    return Response(
                        {"status": "error", "message": "價格不可為負數"}, status=400
                    )
                opt.price = price
                update_fields.append("price")

            is_active = request.data.get("is_active")
            if is_active is not None:
                opt.is_active = bool(is_active)
                update_fields.append("is_active")

        if update_fields:
            opt.save(update_fields=update_fields)

        return api_success(
            {
                "id": opt.pk,
                "name": opt.name,
                "price": opt.price,
                "is_active": opt.is_active,
            }
        )
