from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.utils import timezone

SESSION_TIMEZONE_KEY = "timezone"


def get_zoneinfo(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, TypeError):
        raise ValueError("無效的時區")


def normalize_timezone(timezone_name: str) -> str:
    value = (timezone_name or "").strip()
    if not value:
        raise ValueError("時區不可為空")
    get_zoneinfo(value)
    return value


def get_session_timezone(session) -> str:
    value = session.get(SESSION_TIMEZONE_KEY) if session is not None else ""
    try:
        return normalize_timezone(value)
    except ValueError:
        return settings.TIME_ZONE


def store_session_timezone(session, timezone_name: str) -> str:
    normalized = normalize_timezone(timezone_name)
    session[SESSION_TIMEZONE_KEY] = normalized
    if hasattr(session, "modified"):
        session.modified = True
    return normalized


def convert_store_time_to_user_timezone(
    value: datetime, timezone_name: str
) -> datetime:
    if value is None:
        return value

    store_tz = get_zoneinfo(settings.TIME_ZONE)
    user_tz = get_zoneinfo(timezone_name)
    aware = value if timezone.is_aware(value) else value.replace(tzinfo=store_tz)
    return aware.astimezone(user_tz)
