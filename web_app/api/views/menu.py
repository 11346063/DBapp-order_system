from django.core.exceptions import ValidationError
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from web_app.api.permissions import IsAdmin, IsEmployee
from web_app.api.serializers.menu import MenuDetailSerializer, MenuSerializer
from web_app.api.utils import api_error, api_success
from web_app.models import Menu, Type

# ---------- 共用 inline schema ----------

_ErrorResponse = inline_serializer(
    name="ErrorResponse",
    fields={
        "status": serializers.CharField(default="error"),
        "message": serializers.CharField(),
    },
)

_MenuSuccessResponse = inline_serializer(
    name="MenuSuccessResponse",
    fields={
        "status": serializers.CharField(default="success"),
        "message": serializers.CharField(default="操作成功"),
        "data": MenuSerializer(),
    },
)

_MenuDetailSuccessResponse = inline_serializer(
    name="MenuDetailSuccessResponse",
    fields={
        "status": serializers.CharField(default="success"),
        "message": serializers.CharField(default="操作成功"),
        "data": MenuDetailSerializer(),
    },
)

_MenuToggleSuccessResponse = inline_serializer(
    name="MenuToggleSuccessResponse",
    fields={
        "status": serializers.CharField(default="success"),
        "message": serializers.CharField(default="操作成功"),
        "data": inline_serializer(
            name="MenuToggleData",
            fields={
                "status": serializers.BooleanField(help_text="切換後的上下架狀態"),
                "name": serializers.CharField(help_text="餐點名稱"),
            },
        ),
    },
)


def _validate_uploaded_image(uploaded_file):
    if not uploaded_file:
        return None
    content_type = getattr(uploaded_file, "content_type", "")
    if not content_type.startswith("image/"):
        raise ValidationError("圖片格式不正確")
    return uploaded_file


class MenuDetailAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="取得餐點詳細資訊（含選項）",
        description="依餐點 ID 取得完整資料，包含所有可加購選項。無需登入即可呼叫。",
        tags=["菜單"],
        responses={
            200: OpenApiResponse(
                response=_MenuDetailSuccessResponse,
                description="成功取得餐點詳情",
                examples=[
                    OpenApiExample(
                        "成功範例",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {
                                "id": 1,
                                "name": "雞排",
                                "price": 80,
                                "info": "外皮酥脆、內嫩多汁",
                                "remark": "可加辣、可去骨",
                                "type_id": 1,
                                "type_name": "炸雞類",
                                "status": True,
                                "image_url": "/media/image/chicken.jpg",
                                "options": [
                                    {"id": 1, "name": "小辣", "price": 0},
                                    {"id": 2, "name": "大辣", "price": 0},
                                ],
                            },
                        },
                    )
                ],
            ),
            404: OpenApiResponse(
                response=_ErrorResponse,
                description="找不到指定 ID 的餐點",
                examples=[
                    OpenApiExample(
                        "404 範例",
                        value={"status": "error", "message": "找不到此餐點"},
                    )
                ],
            ),
        },
    )
    def get(self, request, pk):
        try:
            menu = Menu.objects.select_related("type").get(pk=pk)
        except Menu.DoesNotExist:
            return api_error("找不到此餐點", status=404)
        return api_success(MenuDetailSerializer(menu).data)


class MenuToggleAPIView(APIView):
    permission_classes = [IsEmployee]

    @extend_schema(
        summary="切換餐點上下架狀態",
        description=(
            "每次呼叫會反轉目前的上下架狀態（true/false 互換）。\n\n"
            "**權限**：需員工（`identity=E`）或管理員（`identity=A`）身份，"
            "透過 JWT Bearer Token 驗證。"
        ),
        tags=["菜單"],
        request=None,
        responses={
            200: OpenApiResponse(
                response=_MenuToggleSuccessResponse,
                description="切換成功，回傳切換後狀態與餐點名稱",
                examples=[
                    OpenApiExample(
                        "成功範例（已下架）",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {"status": False, "name": "雞排"},
                        },
                    )
                ],
            ),
            401: OpenApiResponse(
                response=_ErrorResponse,
                description="未提供有效的 JWT Token，或 Token 已過期",
            ),
            403: OpenApiResponse(
                response=_ErrorResponse,
                description="身份不符（非員工或管理員，如一般顧客）",
            ),
            404: OpenApiResponse(
                response=_ErrorResponse,
                description="找不到指定 ID 的餐點",
                examples=[
                    OpenApiExample(
                        "404 範例",
                        value={"status": "error", "message": "找不到此商品"},
                    )
                ],
            ),
        },
    )
    def post(self, request, pk):
        try:
            menu = Menu.objects.get(pk=pk)
        except Menu.DoesNotExist:
            return api_error("找不到此商品", status=404)
        menu.status = not menu.status
        menu.save(update_fields=["status"])
        return api_success({"status": menu.status, "name": menu.name})


_MenuEditRequest = inline_serializer(
    name="MenuEditRequest",
    fields={
        "name": serializers.CharField(
            help_text="餐點名稱（必填，全系統唯一）", default="雞排"
        ),
        "price": serializers.IntegerField(
            help_text="基本售價（必填，整數，>= 0）", default=80
        ),
        "type_id": serializers.IntegerField(
            help_text="分類 ID（選填，不填則維持原分類）", required=False
        ),
        "info": serializers.CharField(
            help_text="餐點描述（選填）", required=False, default="外皮酥脆"
        ),
        "remark": serializers.CharField(
            help_text="備註（選填）", required=False, default="可加辣"
        ),
        "file_path": serializers.ImageField(
            help_text="餐點圖片（選填，僅限圖片格式）", required=False
        ),
    },
)

_MenuCreateRequest = inline_serializer(
    name="MenuCreateRequest",
    fields={
        "name": serializers.CharField(
            help_text="餐點名稱（必填，全系統唯一）", default="雞排"
        ),
        "price": serializers.IntegerField(
            help_text="基本售價（必填，整數，>= 0）", default=80
        ),
        "type_id": serializers.IntegerField(help_text="分類 ID（必填）", default=1),
        "info": serializers.CharField(
            help_text="餐點描述（選填）", required=False, default="外皮酥脆"
        ),
        "remark": serializers.CharField(
            help_text="備註（選填）", required=False, default="可加辣"
        ),
        "file_path": serializers.ImageField(
            help_text="餐點圖片（選填，僅限圖片格式）", required=False
        ),
    },
)

_edit_error_examples = [
    OpenApiExample(
        "名稱或價格未填", value={"status": "error", "message": "名稱與價格為必填"}
    ),
    OpenApiExample(
        "價格非整數", value={"status": "error", "message": "價格必須為整數"}
    ),
    OpenApiExample(
        "價格為負數", value={"status": "error", "message": "價格不能為負數"}
    ),
    OpenApiExample("分類不存在", value={"status": "error", "message": "找不到此分類"}),
    OpenApiExample(
        "圖片格式錯誤", value={"status": "error", "message": "圖片格式不正確"}
    ),
]

_edit_responses = {
    200: OpenApiResponse(
        response=_MenuSuccessResponse,
        description="更新成功，回傳更新後的餐點資料",
    ),
    400: OpenApiResponse(
        response=_ErrorResponse,
        description="請求資料有誤（名稱/價格未填、價格非整數、分類不存在、圖片格式錯誤）",
        examples=_edit_error_examples,
    ),
    401: OpenApiResponse(response=_ErrorResponse, description="未提供有效的 JWT Token"),
    403: OpenApiResponse(
        response=_ErrorResponse, description="身份不符（需管理員身份）"
    ),
    404: OpenApiResponse(
        response=_ErrorResponse,
        description="找不到指定 ID 的餐點",
        examples=[
            OpenApiExample(
                "404 範例", value={"status": "error", "message": "找不到此商品"}
            )
        ],
    ),
}


class MenuUpdateAPIView(APIView):
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        summary="更新餐點資料（POST 別名）",
        description=(
            "與 PATCH 行為相同，保留供舊版前端相容。\n\n"
            "**權限**：需管理員身份（`identity=A`）。\n"
            "**Content-Type**：支援 `multipart/form-data`（含圖片上傳）及 `application/json`。"
        ),
        tags=["菜單"],
        request=_MenuEditRequest,
        responses=_edit_responses,
    )
    def post(self, request, pk):
        return self.patch(request, pk)

    @extend_schema(
        summary="更新餐點資料",
        description=(
            "更新指定餐點的名稱、價格、分類、描述、備註或圖片。\n\n"
            "**權限**：需管理員身份（`identity=A`）。\n"
            "**Content-Type**：支援 `multipart/form-data`（含圖片上傳）及 `application/json`（不含圖片）。\n\n"
            "圖片選填；若不傳則保留原圖片。"
        ),
        tags=["菜單"],
        request=_MenuEditRequest,
        responses=_edit_responses,
    )
    def patch(self, request, pk):
        try:
            menu = Menu.objects.select_related("type").get(pk=pk)
        except Menu.DoesNotExist:
            return api_error("找不到此商品", status=404)

        name = request.data.get("name", "").strip()
        price = request.data.get("price")
        if not name or price is None:
            return api_error("名稱與價格為必填")

        try:
            price = int(price)
        except (ValueError, TypeError):
            return api_error("價格必須為整數")

        if price < 0:
            return api_error("價格不能為負數")

        type_id = request.data.get("type_id")
        if type_id:
            try:
                menu.type = Type.objects.get(pk=type_id)
            except Type.DoesNotExist:
                return api_error("找不到此分類")

        try:
            uploaded_image = _validate_uploaded_image(request.FILES.get("file_path"))
        except ValidationError as exc:
            return api_error(exc.message)

        menu.name = name
        menu.price = price
        menu.info = request.data.get("info", "") or ""
        menu.remark = request.data.get("remark", "") or ""
        update_fields = ["name", "price", "info", "remark", "type"]
        if uploaded_image:
            menu.file_path = uploaded_image
            update_fields.append("file_path")
        menu.save(update_fields=update_fields)

        return api_success(MenuSerializer(menu).data)


class MenuCreateAPIView(APIView):
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        summary="新增餐點",
        description=(
            "建立一筆新餐點。\n\n"
            "**權限**：需管理員身份（`identity=A`）。\n"
            "**Content-Type**：支援 `multipart/form-data`（含圖片）及 `application/json`（不含圖片）。\n\n"
            "- `name` 在全系統必須唯一。\n"
            "- `type_id` 必須對應到已存在的分類。"
        ),
        tags=["菜單"],
        request=_MenuCreateRequest,
        responses={
            201: OpenApiResponse(
                response=_MenuSuccessResponse,
                description="建立成功，回傳新餐點資料",
                examples=[
                    OpenApiExample(
                        "建立成功範例",
                        value={
                            "status": "success",
                            "message": "操作成功",
                            "data": {
                                "id": 10,
                                "name": "雞排",
                                "price": 80,
                                "info": "外皮酥脆",
                                "remark": "可加辣",
                                "type_id": 1,
                                "type_name": "炸雞類",
                                "status": True,
                                "image_url": "/media/image/chicken.jpg",
                            },
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                response=_ErrorResponse,
                description="請求資料有誤",
                examples=[
                    OpenApiExample(
                        "必填未填",
                        value={"status": "error", "message": "名稱、價格、分類為必填"},
                    ),
                    OpenApiExample(
                        "價格非整數",
                        value={"status": "error", "message": "價格必須為整數"},
                    ),
                    OpenApiExample(
                        "價格為負數",
                        value={"status": "error", "message": "價格不能為負數"},
                    ),
                    OpenApiExample(
                        "分類不存在",
                        value={"status": "error", "message": "找不到此分類"},
                    ),
                    OpenApiExample(
                        "名稱重複",
                        value={"status": "error", "message": "品項名稱已存在"},
                    ),
                    OpenApiExample(
                        "圖片格式錯誤",
                        value={"status": "error", "message": "圖片格式不正確"},
                    ),
                ],
            ),
            401: OpenApiResponse(
                response=_ErrorResponse, description="未提供有效的 JWT Token"
            ),
            403: OpenApiResponse(
                response=_ErrorResponse, description="身份不符（需管理員身份）"
            ),
        },
    )
    def post(self, request):
        name = request.data.get("name", "").strip()
        price = request.data.get("price")
        type_id = request.data.get("type_id")

        if not name or price is None or not type_id:
            return api_error("名稱、價格、分類為必填")

        try:
            price = int(price)
        except (ValueError, TypeError):
            return api_error("價格必須為整數")

        if price < 0:
            return api_error("價格不能為負數")

        try:
            menu_type = Type.objects.get(pk=type_id)
        except Type.DoesNotExist:
            return api_error("找不到此分類")

        if Menu.objects.filter(name=name).exists():
            return api_error("品項名稱已存在")

        try:
            uploaded_image = _validate_uploaded_image(request.FILES.get("file_path"))
        except ValidationError as exc:
            return api_error(exc.message)

        menu = Menu.objects.create(
            name=name,
            price=price,
            type=menu_type,
            info=request.data.get("info", "") or "",
            remark=request.data.get("remark", "") or "",
            file_path=uploaded_image,
            status=True,
        )

        return api_success(MenuSerializer(menu).data, status=201)
