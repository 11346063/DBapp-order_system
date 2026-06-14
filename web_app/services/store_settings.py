from django.db import transaction
from django.utils import timezone

from web_app.constants import (
    EXTRA_INGREDIENT_COST,
    OPTION_BASIL,
    OPTION_CUT,
    OPTION_GARLIC,
    OPTION_SPICY,
)
from web_app.models import Options
from web_app.models.store_settings import StoreSettings

_DEFAULTS = {
    "extra_ingredient_cost": EXTRA_INGREDIENT_COST,
    "option_name_spicy": OPTION_SPICY,
    "option_name_garlic": OPTION_GARLIC,
    "option_name_basil": OPTION_BASIL,
    "option_name_cut": OPTION_CUT,
}

_OPTION_FIELDS = [
    "option_name_spicy",
    "option_name_garlic",
    "option_name_basil",
    "option_name_cut",
]

_BUSINESS_FIELDS = ["business_hours_enabled", "open_time", "close_time"]


def get_settings() -> StoreSettings:
    try:
        return StoreSettings.objects.get(pk=1)
    except StoreSettings.DoesNotExist:
        obj, _ = StoreSettings.objects.get_or_create(pk=1, defaults=_DEFAULTS)
        return obj


def update_settings(new_data: dict) -> StoreSettings:
    current = get_settings()

    with transaction.atomic():
        for field in _OPTION_FIELDS:
            old_name = getattr(current, field)
            new_name = new_data.get(field, old_name)
            if new_name and new_name != old_name:
                Options.objects.filter(name=old_name).update(name=new_name)

        StoreSettings.objects.filter(pk=1).update(
            **{
                k: v
                for k, v in new_data.items()
                if k
                in {"extra_ingredient_cost"}
                | set(_OPTION_FIELDS)
                | set(_BUSINESS_FIELDS)
            }
        )

    return get_settings()


def is_store_open(settings=None, now=None) -> bool:
    """目前是否在營業時間內。未啟用營業時間限制時一律視為營業中。"""
    s = settings or get_settings()
    if not s.business_hours_enabled:
        return True
    if now is None:
        now = timezone.now()
        # USE_TZ=True 時 now() 為 aware，轉成本地時間；USE_TZ=False 時為 naive，直接用。
        if timezone.is_aware(now):
            now = timezone.localtime(now)
    current = now.time()
    if s.open_time <= s.close_time:
        return s.open_time <= current <= s.close_time
    # 跨午夜營業（例：18:00–02:00）
    return current >= s.open_time or current <= s.close_time


# ---------- 自定義加料選項 CRUD ----------


def get_custom_options():
    return list(Options.objects.filter(is_custom_extra=True).order_by("name"))


def get_active_custom_options():
    return list(
        Options.objects.filter(is_custom_extra=True, is_active=True).order_by("name")
    )


def create_custom_option(name: str, price: int) -> Options:
    name = name.strip()
    if not name:
        raise ValueError("選項名稱不可為空")
    if price < 0:
        raise ValueError("價格不可為負數")
    return Options.objects.create(
        name=name, price=price, is_custom_extra=True, is_active=True
    )


def delete_custom_option(pk: int) -> None:
    Options.objects.filter(pk=pk, is_custom_extra=True).delete()


def toggle_custom_option_active(pk: int) -> bool:
    opt = Options.objects.get(pk=pk, is_custom_extra=True)
    opt.is_active = not opt.is_active
    opt.save(update_fields=["is_active"])
    return opt.is_active
