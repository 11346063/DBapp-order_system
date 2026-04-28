import json
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.contrib import messages
from web_app.forms.register_form import AdminAccountCreateForm
from web_app.models import Identity, Order, OrderItem, User
from web_app.decorators import employee_required, admin_required


def _order_status_counts():
    return {
        0: Order.objects.filter(status=0).count(),
        1: Order.objects.filter(status=1).count(),
        2: Order.objects.filter(status=2).count(),
    }


@employee_required
def staff_order_list(request):
    status_filter = request.GET.get("status", "0")
    try:
        status_val = int(status_filter)
    except (ValueError, TypeError):
        status_val = 0

    orders = (
        Order.objects.filter(status=status_val)
        .select_related("user")
        .order_by("-create_time")
    )

    # 附加每筆訂單的品項
    for order in orders:
        order.items = OrderItem.objects.filter(order=order).select_related("menu")

    status_counts = _order_status_counts()

    return render(
        request,
        "staff/order_list.html",
        {
            "orders": orders,
            "current_status": status_val,
            "status_counts": status_counts,
        },
    )


@employee_required
@require_POST
def staff_update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    data = json.loads(request.body)
    new_status = data.get("status")

    if new_status in [0, 1, 2]:
        order.status = new_status
        order.save()
        return JsonResponse({"success": True, "status_counts": _order_status_counts()})

    return JsonResponse({"error": "無效的狀態"}, status=400)


@admin_required
def staff_report(request):
    now = timezone.now()

    # 日報表（近 30 天）
    thirty_days_ago = now - timedelta(days=30)
    daily = list(
        Order.objects.filter(status=1, create_time__gte=thirty_days_ago)
        .annotate(date=TruncDate("create_time"))
        .values("date")
        .annotate(count=Count("id"), revenue=Sum("price_total"))
        .order_by("date")
    )

    # 月報表（近 12 個月）
    one_year_ago = now - timedelta(days=365)
    monthly = list(
        Order.objects.filter(status=1, create_time__gte=one_year_ago)
        .annotate(month=TruncMonth("create_time"))
        .values("month")
        .annotate(count=Count("id"), revenue=Sum("price_total"))
        .order_by("month")
    )

    # Format for JSON in template
    daily_data = {
        "dates": [d["date"].strftime("%m/%d") for d in daily],
        "counts": [d["count"] for d in daily],
        "revenues": [d["revenue"] or 0 for d in daily],
    }
    monthly_data = {
        "months": [m["month"].strftime("%Y/%m") for m in monthly],
        "counts": [m["count"] for m in monthly],
        "revenues": [m["revenue"] or 0 for m in monthly],
    }

    status_counts = _order_status_counts()

    return render(
        request,
        "staff/report.html",
        {
            "daily_data": json.dumps(daily_data),
            "monthly_data": json.dumps(monthly_data),
            "status_counts": status_counts,
            "current_status": None,
        },
    )


@admin_required
def account_management(request):
    identity_filter = request.GET.get("identity", "")
    allowed_filters = {Identity.ADMIN, Identity.EMPLOYEE, Identity.CUSTOMER}
    accounts = User.objects.order_by("-create_time")
    if identity_filter in allowed_filters:
        accounts = accounts.filter(identity=identity_filter)

    form = AdminAccountCreateForm()
    if request.method == "POST":
        form = AdminAccountCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.identity = form.cleaned_data["identity"]
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "帳號建立成功")
            return redirect("web_app:account_management")

    status_counts = _order_status_counts()
    identity_counts = {
        "all": User.objects.count(),
        Identity.ADMIN: User.objects.filter(identity=Identity.ADMIN).count(),
        Identity.EMPLOYEE: User.objects.filter(identity=Identity.EMPLOYEE).count(),
        Identity.CUSTOMER: User.objects.filter(identity=Identity.CUSTOMER).count(),
    }

    return render(
        request,
        "staff/account_management.html",
        {
            "accounts": accounts,
            "form": form,
            "identity_filter": identity_filter,
            "identity_counts": identity_counts,
            "status_counts": status_counts,
            "current_status": None,
        },
    )
