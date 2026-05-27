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
from web_app.services import store_settings as settings_service

ORDER_PAGE_SIZE = 10


def _attach_order_details(orders):
    """附加品項與 order-level 選項至每筆 order。"""
    for order in orders:
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


@employee_required
def staff_order_list(request):
    view_mode = request.GET.get("view", "list")
    status_counts = order_service.order_status_counts()

    if view_mode == "kanban":
        kanban_groups = {}
        for sv in [0, 1, 2]:
            group = list(
                Order.objects.filter(status=sv)
                .select_related("user")
                .order_by("-created_at")[:20]
            )
            _attach_order_details(group)
            kanban_groups[sv] = group

        kanban_cols = [
            {
                "status": 0,
                "label": "等待接單",
                "icon": "bi-clock",
                "text_class": "text-warning",
                "badge_class": "badge-yellow",
                "count": status_counts.get(0, 0),
                "orders": kanban_groups[0],
            },
            {
                "status": 1,
                "label": "備餐中",
                "icon": "bi-fire",
                "text_class": "text-primary",
                "badge_class": "bg-primary",
                "count": status_counts.get(1, 0),
                "orders": kanban_groups[1],
            },
            {
                "status": 2,
                "label": "可取餐",
                "icon": "bi-bell",
                "text_class": "text-info",
                "badge_class": "bg-info text-dark",
                "count": status_counts.get(2, 0),
                "orders": kanban_groups[2],
            },
        ]

        return render(
            request,
            "staff/order_list.html",
            {
                "view_mode": "kanban",
                "kanban_cols": kanban_cols,
                "current_status": None,
                "status_counts": status_counts,
            },
        )

    # --- 清單模式 ---
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
    _attach_order_details(paged_orders)

    return render(
        request,
        "staff/order_list.html",
        {
            "view_mode": "list",
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


@admin_required
def staff_settings_view(request):
    status_counts = order_service.order_status_counts()
    if request.method == "POST":
        try:
            extra_cost = int(request.POST.get("extra_ingredient_cost", 10))
            if extra_cost < 0:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, _("加料單價必須是非負整數"))
            return redirect("web_app:staff_settings")

        new_data = {
            "extra_ingredient_cost": extra_cost,
            "option_name_spicy": request.POST.get("option_name_spicy", "").strip(),
            "option_name_garlic": request.POST.get("option_name_garlic", "").strip(),
            "option_name_basil": request.POST.get("option_name_basil", "").strip(),
            "option_name_cut": request.POST.get("option_name_cut", "").strip(),
        }
        for key, val in new_data.items():
            if key != "extra_ingredient_cost" and not val:
                messages.error(request, _("選項名稱不可為空"))
                return redirect("web_app:staff_settings")

        settings_service.update_settings(new_data)
        messages.success(request, _("系統設定已更新"))
        return redirect("web_app:staff_settings")

    return render(
        request,
        "staff/settings.html",
        {
            "settings": settings_service.get_settings(),
            "status_counts": status_counts,
            "current_status": None,
        },
    )
