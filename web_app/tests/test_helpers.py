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

_SYSTEM_OPTIONS = [
    (SPICY_OPTION_ID, "辣度", 0),
    (GARLIC_OPTION_ID, "加蒜", 10),
    (BASIL_OPTION_ID, "九層塔", 10),
    (CUT_OPTION_ID, "切", 0),
]


def seed_system_options():
    # bulk_create(ignore_conflicts=True) → MySQL INSERT IGNORE.
    # Existing rows are silently skipped with no exclusive lock, avoiding
    # InnoDB deadlocks that occur when UPDATE/SELECT FOR UPDATE compete for
    # the same fixed-PK rows inside TestCase nested savepoints.
    Options.objects.bulk_create(
        [Options(id=pk, name=name, price=price) for pk, name, price in _SYSTEM_OPTIONS],
        ignore_conflicts=True,
    )
