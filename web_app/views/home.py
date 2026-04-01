from django.shortcuts import render
from django.http import JsonResponse
from web_app.models import Menu, Type, OptGroup


def home_view(request):
    types = Type.objects.all()
    menus = Menu.objects.select_related('type').all()
    return render(request, 'home.html', {
        'types': types,
        'menus': menus,
    })


def menu_detail_api(request, pk):
    try:
        menu = Menu.objects.select_related('type').get(pk=pk)
    except Menu.DoesNotExist:
        return JsonResponse({'error': '找不到此餐點'}, status=404)

    opt_groups = OptGroup.objects.filter(menu=menu).select_related('opt')
    options = [
        {
            'id': og.opt.id,
            'name': og.opt.name,
            'price': og.opt.price,
        }
        for og in opt_groups
    ]

    data = {
        'id': menu.id,
        'name': menu.name,
        'price': menu.price,
        'info': menu.info or '',
        'remark': menu.remark or '',
        'type_name': menu.type.type_name,
        'options': options,
    }

    
    return JsonResponse(data)
