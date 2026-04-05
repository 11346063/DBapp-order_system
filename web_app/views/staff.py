import json
from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
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


@login_required
@staff_member_required
def staff_report(request):
    # Only admin (identity='A') or superuser can access reports
    if not (request.user.identity == 'A' or request.user.is_superuser):
        return HttpResponseForbidden('權限不足')

    now = timezone.now()

    # Daily report (last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    daily = list(
        Order.objects.filter(status=1, create_time__gte=thirty_days_ago)
        .annotate(date=TruncDate('create_time'))
        .values('date')
        .annotate(count=Count('id'), revenue=Sum('price_total'))
        .order_by('date')
    )

    # Monthly report (last 12 months)
    one_year_ago = now - timedelta(days=365)
    monthly = list(
        Order.objects.filter(status=1, create_time__gte=one_year_ago)
        .annotate(month=TruncMonth('create_time'))
        .values('month')
        .annotate(count=Count('id'), revenue=Sum('price_total'))
        .order_by('month')
    )

    # Format for JSON in template
    daily_data = {
        'dates': [d['date'].strftime('%m/%d') for d in daily],
        'counts': [d['count'] for d in daily],
        'revenues': [d['revenue'] or 0 for d in daily],
    }
    monthly_data = {
        'months': [m['month'].strftime('%Y/%m') for m in monthly],
        'counts': [m['count'] for m in monthly],
        'revenues': [m['revenue'] or 0 for m in monthly],
    }

    status_counts = {
        0: Order.objects.filter(status=0).count(),
        1: Order.objects.filter(status=1).count(),
        2: Order.objects.filter(status=2).count(),
    }

    return render(request, 'staff/report.html', {
        'daily_data': json.dumps(daily_data),
        'monthly_data': json.dumps(monthly_data),
        'status_counts': status_counts,
    })
