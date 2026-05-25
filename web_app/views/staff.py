import json
from datetime import timedelta
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.contrib import messages
from web_app.forms.register_form import AdminAccountCreateForm
from web_app.models import Identity, Order, OrderItem, OrderItemOption, User
from web_app.decorators import employee_required, admin_required
from web_app.services import order as order_service

ORDER_PAGE_SIZE = 10


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
        .order_by("-created_at")
    )

    paginator = Paginator(orders, ORDER_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))
    paged_orders = list(page_obj.object_list)

    # 附加品項（含 item-level 選項）與 order-level 選項
    for order in paged_orders:
        order.items = (
            OrderItem.objects.filter(order=order)
            .select_related("menu")
            .prefetch_related("orderitemoption_set__opt")
        )
        raw_opts = OrderItemOption.objects.filter(
            order=order, order_item=None
        ).select_related("opt")
        order.order_opts = order_service.format_order_options(raw_opts)
        order.order_opts_tags = order_service.format_order_option_tags(raw_opts)

    status_counts = order_service.order_status_counts()

    return render(
        request,
        "staff/order_list.html",
        {
            "orders": paged_orders,
            "page_obj": page_obj,
            "current_status": status_val,
            "status_counts": status_counts,
        },
    )


@admin_required
def staff_report(request):
    now = timezone.now()

    # 日報表（近 30 天）
    thirty_days_ago = now - timedelta(days=30)
    daily = list(
        Order.objects.filter(
            status=Order.OrderStatus.COMPLETED, created_at__gte=thirty_days_ago
        )
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"), revenue=Sum("price_total"))
        .order_by("date")
    )

    # 月報表（近 12 個月）
    one_year_ago = now - timedelta(days=365)
    monthly = list(
        Order.objects.filter(
            status=Order.OrderStatus.COMPLETED, created_at__gte=one_year_ago
        )
        .annotate(month=TruncMonth("created_at"))
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

    status_counts = order_service.order_status_counts()

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
    accounts = User.objects.order_by("-created_at")
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
            messages.success(request, _("帳號建立成功"))
            return redirect("web_app:account_management")

    status_counts = order_service.order_status_counts()
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
