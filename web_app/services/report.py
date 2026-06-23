"""營運報表查詢：日期區間解析、每日銷售、熱銷品項。

純查詢邏輯集中於此，供 staff_report（async view 以 sync_to_async 包裝）
與 CSV 匯出共用，並便於單元測試。
"""

from datetime import date, datetime, timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate

from web_app.models import Order, OrderItem

_DEFAULT_RANGE_DAYS = 30


def parse_date_range(start_str, end_str, today=None):
    """解析 YYYY-MM-DD 區間；缺漏、格式錯誤或 start>end 時回退為近 30 天。"""
    today = today or date.today()
    default_start = today - timedelta(days=_DEFAULT_RANGE_DAYS - 1)

    def _parse(value, fallback):
        if not value:
            return fallback
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return fallback

    start = _parse(start_str, default_start)
    end = _parse(end_str, today)
    if start > end:
        return default_start, today
    return start, end


def daily_sales(start_date, end_date):
    """區間內每日已完成訂單的筆數與營業額。"""
    return list(
        Order.objects.filter(
            status=Order.OrderStatus.COMPLETED,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"), revenue=Sum("price_total"))
        .order_by("date")
    )


def completed_summary(start_date, end_date):
    """區間內已完成訂單的筆數與總營業額（已完成 = 已收款）。"""
    from django.db.models import Count, Sum

    row = Order.objects.filter(
        status=Order.OrderStatus.COMPLETED,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    ).aggregate(count=Count("id"), revenue=Sum("price_total"))
    return {"count": row["count"] or 0, "revenue": row["revenue"] or 0}


def top_selling_items(start_date, end_date, limit=10):
    """區間內已完成訂單的熱銷品項排行（依數量遞減）。"""
    return list(
        OrderItem.objects.filter(
            order__status=Order.OrderStatus.COMPLETED,
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date,
        )
        .values("menu__name")
        .annotate(qty=Sum("amount"), revenue=Sum("total_price"))
        .order_by("-qty")[:limit]
    )
