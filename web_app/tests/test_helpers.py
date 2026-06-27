"""
共用測試輔助工具。

seed_system_options()：確保系統選項（辣度/加蒜/九層塔/切）的 Options 記錄存在。
任何需要呼叫 create_order_from_cart 或 create_staff_order 的 TestCase.setUp 應先呼叫此函式。
"""

from web_app.constants import (
    BASIL_OPTION_ID,
    CUT_OPTION_ID,
    GARLIC_OPTION_ID,
    SPICY_OPTION_ID,
)
from web_app.models import Options


def seed_system_options():
    Options.objects.update_or_create(
        pk=SPICY_OPTION_ID, defaults={"name": "辣度", "price": 0}
    )
    Options.objects.update_or_create(
        pk=GARLIC_OPTION_ID, defaults={"name": "加蒜", "price": 10}
    )
    Options.objects.update_or_create(
        pk=BASIL_OPTION_ID, defaults={"name": "九層塔", "price": 10}
    )
    Options.objects.update_or_create(
        pk=CUT_OPTION_ID, defaults={"name": "切", "price": 0}
    )
