from django.core.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from web_app.api.permissions import IsAdmin, IsEmployee
from web_app.api.serializers.menu import MenuDetailSerializer, MenuSerializer
from web_app.api.utils import api_error, api_success
from web_app.models import Menu, Type


def _validate_uploaded_image(uploaded_file):
    if not uploaded_file:
        return None
    content_type = getattr(uploaded_file, "content_type", "")
    if not content_type.startswith("image/"):
        raise ValidationError("圖片格式不正確")
    return uploaded_file


class MenuDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            menu = Menu.objects.select_related("type").get(pk=pk)
        except Menu.DoesNotExist:
            return api_error("找不到此餐點", status=404)
        return api_success(MenuDetailSerializer(menu).data)


class MenuToggleAPIView(APIView):
    permission_classes = [IsEmployee]

    def post(self, request, pk):
        try:
            menu = Menu.objects.get(pk=pk)
        except Menu.DoesNotExist:
            return api_error("找不到此商品", status=404)
        menu.status = not menu.status
        menu.save(update_fields=["status"])
        return api_success({"status": menu.status, "name": menu.name})


class MenuUpdateAPIView(APIView):
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, pk):
        return self.patch(request, pk)

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
