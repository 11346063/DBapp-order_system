import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from web_app.models import Identity
from web_app.services import menu as menu_service
from web_app.services.exceptions import NotFoundError, ValidationServiceError

_DUMPS = {"ensure_ascii": False}


def _json(data, status=200):
    """統一回傳 UTF-8 JSON（中文不轉義）"""
    return JsonResponse(data, status=status, json_dumps_params=_DUMPS)


def _parse_menu_request(request):
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        return request.POST

    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return None


def _check_staff_permission(request):
    """
    回傳 None 表示通過，否則回傳對應的 HttpResponse。
    未登入 → 302 重導向登入頁
    非員工/管理員 → 403
    """
    if not request.user.is_authenticated:
        return redirect("web_app:login")
    if request.user.identity not in (Identity.ADMIN, Identity.EMPLOYEE):
        return _json({"status": "error", "message": "權限不足"}, status=403)
    return None


def _check_admin_permission(request):
    if not request.user.is_authenticated:
        return redirect("web_app:login")
    if request.user.identity != Identity.ADMIN:
        return _json({"status": "error", "message": "權限不足"}, status=403)
    return None


@require_POST
def menu_toggle_status(request, pk):
    """切換商品上下架狀態（員工/管理員）"""
    denied = _check_staff_permission(request)
    if denied:
        return denied

    try:
        return _json(menu_service.toggle_menu_status(pk))
    except NotFoundError as exc:
        return _json(
            {"status": "error", "message": exc.message}, status=exc.status_code
        )


@require_POST
def menu_edit(request, pk):
    """編輯品項資料（管理員）"""
    denied = _check_admin_permission(request)
    if denied:
        return denied

    data = _parse_menu_request(request)
    if data is None:
        return _json({"status": "error", "message": "無效的 JSON"}, status=400)

    try:
        menu = menu_service.update_menu_item(
            pk,
            data,
            request.FILES.get("file_path"),
        )
    except NotFoundError as exc:
        return _json(
            {"status": "error", "message": exc.message}, status=exc.status_code
        )
    except ValidationServiceError as exc:
        return _json(
            {"status": "error", "message": exc.message}, status=exc.status_code
        )

    return _json(menu_service.menu_payload(menu))


@require_POST
def menu_create(request):
    """新增品項（管理員）"""
    denied = _check_admin_permission(request)
    if denied:
        return denied

    data = _parse_menu_request(request)
    if data is None:
        return _json({"status": "error", "message": "無效的 JSON"}, status=400)

    try:
        menu = menu_service.create_menu_item(data, request.FILES.get("file_path"))
    except ValidationServiceError as exc:
        return _json(
            {"status": "error", "message": exc.message}, status=exc.status_code
        )

    return _json(menu_service.menu_payload(menu), status=201)
