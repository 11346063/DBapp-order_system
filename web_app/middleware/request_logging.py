import logging
import time

from django.conf import settings

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        # 於 request 期間讀取設定，使開關可在 runtime / 測試中切換
        if getattr(settings, "ENABLE_REQUEST_LOGGING", False):
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "user_id": getattr(request.user, "pk", None),
                    "ms": int((time.monotonic() - start) * 1000),
                },
            )
        return response
