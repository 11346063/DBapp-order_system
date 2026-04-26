from django.shortcuts import render
from django.http import JsonResponse
from web_app.models import Menu, Type, OptGroup, Identity


def home_view(request):
    types = Type.objects.all()
    user = request.user
    is_staff = user.is_authenticated and user.identity in (
        Identity.ADMIN,
        Identity.EMPLOYEE,
    )
    if is_staff:
        menus = Menu.objects.select_related("type").all()
    else:
        menus = Menu.objects.select_related("type").filter(status=True)
    return render(
        request,
        "home.html",
        {
            "types": types,
            "menus": menus,
            "is_staff": is_staff,
        },
    )


def _menu_image_url(menu):
    if not menu.file_path:
        return ""
    return menu.file_path.url


def menu_detail_api(request, pk):
    try:
        menu = Menu.objects.select_related("type").get(pk=pk)
    except Menu.DoesNotExist:
        return JsonResponse({"error": "找不到此餐點"}, status=404)

    opt_groups = OptGroup.objects.filter(menu=menu).select_related("opt")
    options = [
        {
            "id": og.opt.id,
            "name": og.opt.name,
            "price": og.opt.price,
        }
        for og in opt_groups
    ]

    data = {
        "id": menu.id,
        "name": menu.name,
        "price": menu.price,
        "info": menu.info or "",
        "remark": menu.remark or "",
        "type_id": menu.type_id,
        "type_name": menu.type.type_name,
        "status": menu.status,
        "image_url": _menu_image_url(menu),
        "options": options,
    }

    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
