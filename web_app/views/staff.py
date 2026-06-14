import asyncio
import csv
import json
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db.models import Count, Prefetch, Q, Sum
from django.db.models.functions import TruncMonth
from django.contrib import messages
from web_app.forms.register_form import AdminAccountCreateForm
from web_app.models import Identity, Order, OrderItem, OrderItemOption, User
from web_app.decorators import employee_required, admin_required
from web_app.services import order as order_service
from web_app.services import report as report_service
from web_app.services import store_settings as settings_service

ORDER_PAGE_SIZE = 10


def _prefetch_order_details(queryset):
    """在 queryset 層一次 prefetch 訂單品項與選項，避免 N+1。"""
    return queryset.prefetch_related(
        Prefetch(
            "orderitem_set",
            queryset=OrderItem.objects.select_related("menu").prefetch_related(
                Prefetch(
                    "orderitemoption_set",
                    queryset=OrderItemOption.objects.select_related("opt"),
                )
            ),
        ),
        Prefetch(
            "orderitemoption_set",
            queryset=OrderItemOption.objects.filter(order_item=None).select_related(
                "opt"
            ),
            to_attr="order_level_opts",
        ),
    )


def _attach_order_details(orders, store_settings=None):
    """從已 prefetch 的 queryset 附加品項與 order-level 選項（不發額外 DB 查詢）。"""
    if not orders:
        return
    s = store_settings or settings_service.get_settings()
    for order in orders:
        order.items = order.orderitem_set.all()
        raw_opts = order.order_level_opts
        order.order_opts = order_service.format_order_options(raw_opts, s)
        order.order_opts_tags = order_service.format_order_option_tags(raw_opts, s)


@employee_required
def staff_order_list(request):
    view_mode = request.GET.get("view", "list")
    status_counts = order_service.order_status_counts()

    if view_mode == "kanban":
        store_settings = settings_service.get_settings()
        kanban_groups = {}
        for sv in [0, 1, 2]:
            group = list(
                _prefetch_order_details(
                    Order.objects.filter(status=sv)
                    .select_related("user")
                    .order_by("-created_at")
                )[:20]
            )
            _attach_order_details(group, store_settings)
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

    store_settings = settings_service.get_settings()
    orders = _prefetch_order_details(
        Order.objects.filter(status=status_val)
        .select_related("user")
        .order_by("-created_at")
    )

    paginator = Paginator(orders, ORDER_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))
    paged_orders = list(page_obj.object_list)
    _attach_order_details(paged_orders, store_settings)

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
async def staff_report(request):
    now = timezone.now()
    one_year_ago = now - timedelta(days=365)

    start_date, end_date = report_service.parse_date_range(
        request.GET.get("start", ""), request.GET.get("end", "")
    )

    monthly_qs = (
        Order.objects.filter(
            status=Order.OrderStatus.COMPLETED, created_at__gte=one_year_ago
        )
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"), revenue=Sum("price_total"))
        .order_by("month")
    )

    # 並行發出查詢
    daily, top_items, monthly, status_counts = await asyncio.gather(
        sync_to_async(report_service.daily_sales)(start_date, end_date),
        sync_to_async(report_service.top_selling_items)(start_date, end_date),
        sync_to_async(list)(monthly_qs),
        order_service.async_order_status_counts(),
    )

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

    return render(
        request,
        "staff/report.html",
        {
            "daily_data": json.dumps(daily_data),
            "monthly_data": json.dumps(monthly_data),
            "top_items": top_items,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "status_counts": status_counts,
            "current_status": None,
        },
    )


@admin_required
def staff_report_export(request):
    """匯出選定區間每日銷售為 CSV（Excel 相容，含 UTF-8 BOM）。"""
    start_date, end_date = report_service.parse_date_range(
        request.GET.get("start", ""), request.GET.get("end", "")
    )
    rows = report_service.daily_sales(start_date, end_date)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="report_{start_date}_{end_date}.csv"'
    )
    response.write("﻿")  # BOM，讓 Excel 正確辨識 UTF-8 中文
    writer = csv.writer(response)
    writer.writerow(["日期", "訂單數", "營業額"])
    for r in rows:
        writer.writerow([r["date"].strftime("%Y-%m-%d"), r["count"], r["revenue"] or 0])
    return response


@admin_required
async def account_management(request):
    identity_filter = request.GET.get("identity", "")
    allowed_filters = {Identity.ADMIN, Identity.EMPLOYEE, Identity.CUSTOMER}

    form = AdminAccountCreateForm()
    if request.method == "POST":
        form = AdminAccountCreateForm(request.POST)
        # form.is_valid() 包含 DB 唯一值查詢，需在 sync 上下文執行
        if await sync_to_async(form.is_valid)():
            user = form.save(commit=False)
            user.identity = form.cleaned_data["identity"]
            user.set_password(form.cleaned_data["password"])
            await sync_to_async(user.save)()
            messages.success(request, _("帳號建立成功"))
            return redirect("web_app:account_management")

    accounts_qs = User.objects.order_by("-created_at")
    if identity_filter in allowed_filters:
        accounts_qs = accounts_qs.filter(identity=identity_filter)

    # 三個查詢並行發出
    accounts, status_counts, identity_agg = await asyncio.gather(
        sync_to_async(list)(accounts_qs),
        order_service.async_order_status_counts(),
        User.objects.aaggregate(
            all=Count("pk"),
            admin=Count("pk", filter=Q(identity=Identity.ADMIN)),
            employee=Count("pk", filter=Q(identity=Identity.EMPLOYEE)),
            customer=Count("pk", filter=Q(identity=Identity.CUSTOMER)),
        ),
    )

    identity_counts = {
        "all": identity_agg["all"],
        Identity.ADMIN: identity_agg["admin"],
        Identity.EMPLOYEE: identity_agg["employee"],
        Identity.CUSTOMER: identity_agg["customer"],
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
        action = request.POST.get("action", "save_settings")

        if action == "add_custom_option":
            name = request.POST.get("new_option_name", "").strip()
            try:
                price = int(request.POST.get("new_option_price", 0))
                if price < 0:
                    raise ValueError
            except (TypeError, ValueError):
                messages.error(request, _("價格必須是非負整數"))
                return redirect("web_app:staff_settings")
            try:
                settings_service.create_custom_option(name, price)
                messages.success(request, _("選項已新增"))
            except ValueError as exc:
                messages.error(request, str(exc))
            return redirect("web_app:staff_settings")

        if action == "delete_custom_option":
            option_id = request.POST.get("option_id")
            if option_id:
                settings_service.delete_custom_option(int(option_id))
                messages.success(request, _("選項已刪除"))
            return redirect("web_app:staff_settings")

        if action == "toggle_custom_option":
            option_id = request.POST.get("option_id")
            if option_id:
                settings_service.toggle_custom_option_active(int(option_id))
            return redirect("web_app:staff_settings")

        # default: save_settings
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

        try:
            open_time = datetime.strptime(
                request.POST.get("open_time", "").strip(), "%H:%M"
            ).time()
            close_time = datetime.strptime(
                request.POST.get("close_time", "").strip(), "%H:%M"
            ).time()
        except ValueError:
            messages.error(request, _("營業時間格式錯誤（需為 HH:MM）"))
            return redirect("web_app:staff_settings")

        new_data["business_hours_enabled"] = (
            request.POST.get("business_hours_enabled") == "on"
        )
        new_data["open_time"] = open_time
        new_data["close_time"] = close_time

        settings_service.update_settings(new_data)
        messages.success(request, _("系統設定已更新"))
        return redirect("web_app:staff_settings")

    return render(
        request,
        "staff/settings.html",
        {
            "settings": settings_service.get_settings(),
            "custom_options": settings_service.get_custom_options(),
            "status_counts": status_counts,
            "current_status": None,
        },
    )
