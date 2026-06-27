from django.utils import timezone

from web_app.models import Options
from web_app.models.store_settings import StoreSettings

_BUSINESS_FIELDS = ["business_hours_enabled", "open_time", "close_time"]


def get_settings() -> StoreSettings:
    obj, _ = StoreSettings.objects.get_or_create(pk=1)
    return obj


def update_settings(new_data: dict) -> StoreSettings:
    allowed = set(_BUSINESS_FIELDS)
    StoreSettings.objects.filter(pk=1).update(
        **{k: v for k, v in new_data.items() if k in allowed}
    )
    return get_settings()


def is_store_open(settings=None, now=None) -> bool:
    """目前是否在營業時間內。未啟用營業時間限制時一律視為營業中。"""
    s = settings or get_settings()
    if not s.business_hours_enabled:
        return True
    if now is None:
        now = timezone.now()
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
