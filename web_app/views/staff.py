import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from web_app.models import Order, OrderItem


@login_required
@staff_member_required
def staff_order_list(request):
    status_filter = request.GET.get('status', '0')
    try:
        status_val = int(status_filter)
    except (ValueError, TypeError):
        status_val = 0

    orders = Order.objects.filter(status=status_val).select_related('user').order_by('-create_time')

    # Attach items to each order
    for order in orders:
        order.items = OrderItem.objects.filter(order=order).select_related('menu')

    status_counts = {
        0: Order.objects.filter(status=0).count(),
        1: Order.objects.filter(status=1).count(),
        2: Order.objects.filter(status=2).count(),
    }

    return render(request, 'staff/order_list.html', {
        'orders': orders,
        'current_status': status_val,
        'status_counts': status_counts,
    })


@login_required
@staff_member_required
@require_POST
def staff_update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    data = json.loads(request.body)
    new_status = data.get('status')

    if new_status in [0, 1, 2]:
        order.status = new_status
        order.save()
        return JsonResponse({'success': True})

    return JsonResponse({'error': '無效的狀態'}, status=400)
