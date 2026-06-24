from django import template
from django.utils.dateformat import format as date_format

from web_app.utils.timezone import (
    convert_store_time_to_user_timezone,
    get_session_timezone,
)

register = template.Library()


@register.simple_tag(takes_context=True)
def local_user_time(context, value, fmt="Y/m/d H:i"):
    if value is None:
        return ""

    request = context.get("request")
    timezone_name = get_session_timezone(getattr(request, "session", None))
    local_value = convert_store_time_to_user_timezone(value, timezone_name)
    return date_format(local_value, fmt)
