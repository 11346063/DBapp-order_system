import json
import logging
from functools import wraps

from django.http import JsonResponse

logger = logging.getLogger(__name__)


def handle_api_exceptions(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "JSON 格式錯誤"}, status=400)
        except KeyError as exc:
            return JsonResponse(
                {"success": False, "error": f"缺少必要欄位：{exc.args[0]}"},
                status=400,
                json_dumps_params={"ensure_ascii": False},
            )
        except (TypeError, ValueError):
            return JsonResponse({"success": False, "error": "資料格式錯誤"}, status=400)
        except Exception:
            logger.exception("Unhandled API exception in %s", view_func.__name__)
            return JsonResponse(
                {"success": False, "error": "系統暫時無法處理請求"},
                status=500,
            )

    return wrapper

