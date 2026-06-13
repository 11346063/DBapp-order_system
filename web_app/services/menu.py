from datetime import date

from django.db.models import Q

from web_app.models import Identity, Menu, Type
from web_app.services.exceptions import NotFoundError, ValidationServiceError


def validate_uploaded_image(uploaded_file):
    if not uploaded_file:
        return None

    content_type = getattr(uploaded_file, "content_type", "")
    if not content_type.startswith("image/"):
        raise ValidationServiceError("圖片格式不正確")
    return uploaded_file


def menu_image_url(menu):
    if not menu.file_path:
        return ""
    return menu.file_path.url


def menu_payload(menu):
    return {
        "id": menu.pk,
        "name": menu.name,
        "price": menu.price,
        "info": menu.info,
        "remark": menu.remark,
        "type_id": menu.type_id,
        "type_name": menu.type.type_name,
        "status": menu.status,
        "image_url": menu_image_url(menu),
    }


def get_menu_detail(menu_id):
    try:
        return Menu.objects.select_related("type").get(pk=menu_id)
    except Menu.DoesNotExist as exc:
        raise NotFoundError("找不到此餐點") from exc


def toggle_menu_status(menu_id):
    try:
        menu = Menu.objects.get(pk=menu_id)
    except Menu.DoesNotExist as exc:
        raise NotFoundError("找不到此商品") from exc

    menu.status = not menu.status
    menu.save(update_fields=["status"])
    return {"status": menu.status, "name": menu.name}


def toggle_menu_sold_out_today(menu_id):
    try:
        menu = Menu.objects.get(pk=menu_id)
    except Menu.DoesNotExist as exc:
        raise NotFoundError("找不到此商品") from exc

    today = date.today()
    menu.today_sold_out = today if menu.today_sold_out != today else None
    menu.save(update_fields=["today_sold_out"])
    return {"sold_out_today": menu.today_sold_out == today, "name": menu.name}


def _clean_required_menu_fields(data, *, require_type):
    name = data.get("name", "").strip()
    price = data.get("price")
    type_id = data.get("type_id")

    if require_type:
        if not name or price is None or not type_id:
            raise ValidationServiceError("名稱、價格、分類為必填")
    elif not name or price is None:
        raise ValidationServiceError("名稱與價格為必填")

    try:
        price = int(price)
    except (ValueError, TypeError) as exc:
        raise ValidationServiceError("價格必須為整數") from exc

    if price < 0:
        raise ValidationServiceError("價格不能為負數")

    return name, price, type_id


def _get_type(type_id):
    try:
        return Type.objects.get(pk=type_id)
    except Type.DoesNotExist as exc:
        raise ValidationServiceError("找不到此分類") from exc


def create_menu_item(data, uploaded_image=None):
    name, price, type_id = _clean_required_menu_fields(data, require_type=True)
    menu_type = _get_type(type_id)

    if Menu.objects.filter(name=name).exists():
        raise ValidationServiceError("品項名稱已存在")

    uploaded_image = validate_uploaded_image(uploaded_image)
    return Menu.objects.create(
        name=name,
        price=price,
        type=menu_type,
        info=data.get("info", "") or "",
        remark=data.get("remark", "") or "",
        file_path=uploaded_image,
        status=True,
    )


def update_menu_item(menu_id, data, uploaded_image=None):
    try:
        menu = Menu.objects.select_related("type").get(pk=menu_id)
    except Menu.DoesNotExist as exc:
        raise NotFoundError("找不到此商品") from exc

    name, price, type_id = _clean_required_menu_fields(data, require_type=False)
    if type_id:
        menu.type = _get_type(type_id)

    uploaded_image = validate_uploaded_image(uploaded_image)
    menu.name = name
    menu.price = price
    menu.info = data.get("info", "") or ""
    menu.remark = data.get("remark", "") or ""
    update_fields = ["name", "price", "info", "remark", "type"]
    if uploaded_image:
        menu.file_path = uploaded_image
        update_fields.append("file_path")
    menu.save(update_fields=update_fields)
    return menu


def search_menus(queryset, query):
    if not query:
        return queryset
    return queryset.filter(
        Q(name__icontains=query)
        | Q(info__icontains=query)
        | Q(remark__icontains=query)
        | Q(type__type_name__icontains=query)
    )


def _sort(queryset, query):
    return search_menus(queryset, query).order_by("type__type_name", "name")


def visible_menus_for_user(user, query=""):
    if user.is_authenticated and user.identity in (Identity.ADMIN, Identity.EMPLOYEE):
        menus = Menu.objects.select_related("type").all()
    else:
        menus = Menu.objects.select_related("type").filter(status=True)
    return _sort(menus, query)


def assisted_ordering_menus(query=""):
    return _sort(Menu.objects.select_related("type").filter(status=True), query)
