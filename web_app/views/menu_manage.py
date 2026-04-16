import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from web_app.models import Menu, Type, Identity

_DUMPS = {'ensure_ascii': False}


def _json(data, status=200):
    """統一回傳 UTF-8 JSON（中文不轉義）"""
    return JsonResponse(data, status=status, json_dumps_params=_DUMPS)


def _check_staff_permission(request):
    """
    回傳 None 表示通過，否則回傳對應的 HttpResponse。
    未登入 → 302 重導向登入頁
    非員工/管理員 → 403
    """
    if not request.user.is_authenticated:
        return redirect('web_app:login')
    if request.user.identity not in (Identity.ADMIN, Identity.EMPLOYEE):
        return _json({'error': '權限不足'}, status=403)
    return None


@require_POST
def menu_toggle_status(request, pk):
    """切換商品上下架狀態（員工/管理員）"""
    denied = _check_staff_permission(request)
    if denied:
        return denied

    try:
        menu = Menu.objects.get(pk=pk)
    except Menu.DoesNotExist:
        return _json({'error': '找不到此商品'}, status=404)

    menu.status = not menu.status
    menu.save(update_fields=['status'])

    return _json({'status': menu.status, 'name': menu.name})


@require_POST
def menu_edit(request, pk):
    """編輯品項資料（員工/管理員）"""
    denied = _check_staff_permission(request)
    if denied:
        return denied

    try:
        menu = Menu.objects.get(pk=pk)
    except Menu.DoesNotExist:
        return _json({'error': '找不到此商品'}, status=404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return _json({'error': '無效的 JSON'}, status=400)

    name = data.get('name', '').strip()
    price = data.get('price')
    if not name or price is None:
        return _json({'error': '名稱與價格為必填'}, status=400)

    try:
        price = int(price)
    except (ValueError, TypeError):
        return _json({'error': '價格必須為整數'}, status=400)

    type_id = data.get('type_id')
    if type_id:
        try:
            menu.type = Type.objects.get(pk=type_id)
        except Type.DoesNotExist:
            return _json({'error': '找不到此分類'}, status=400)

    menu.name = name
    menu.price = price
    menu.info = data.get('info', '') or ''
    menu.remark = data.get('remark', '') or ''
    menu.save(update_fields=['name', 'price', 'info', 'remark', 'type'])

    return _json({
        'id': menu.pk,
        'name': menu.name,
        'price': menu.price,
        'info': menu.info,
        'remark': menu.remark,
        'type_id': menu.type_id,
        'type_name': menu.type.type_name,
    })


@require_POST
def menu_create(request):
    """新增品項（員工/管理員）"""
    denied = _check_staff_permission(request)
    if denied:
        return denied

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return _json({'error': '無效的 JSON'}, status=400)

    name = data.get('name', '').strip()
    price = data.get('price')
    type_id = data.get('type_id')

    if not name or price is None or not type_id:
        return _json({'error': '名稱、價格、分類為必填'}, status=400)

    try:
        price = int(price)
    except (ValueError, TypeError):
        return _json({'error': '價格必須為整數'}, status=400)

    try:
        menu_type = Type.objects.get(pk=type_id)
    except Type.DoesNotExist:
        return _json({'error': '找不到此分類'}, status=400)

    if Menu.objects.filter(name=name).exists():
        return _json({'error': '品項名稱已存在'}, status=400)

    menu = Menu.objects.create(
        name=name,
        price=price,
        type=menu_type,
        info=data.get('info', '') or '',
        remark=data.get('remark', '') or '',
        status=True,
    )

    return _json({
        'id': menu.pk,
        'name': menu.name,
        'price': menu.price,
        'info': menu.info,
        'remark': menu.remark,
        'type_id': menu.type_id,
        'type_name': menu.type.type_name,
        'status': menu.status,
    }, status=201)
