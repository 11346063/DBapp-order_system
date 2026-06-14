"""
Middleware 規劃 M1/M4：RequestLoggingMiddleware 測試缺口補齊。

直接以 RequestFactory 驅動 middleware，不依賴 views/DB，
驗證開關行為與記錄欄位。
"""

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from web_app.middleware.request_logging import RequestLoggingMiddleware

_LOGGER = "web_app.middleware.request_logging"


class RequestLoggingMiddlewareTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _run(self, status=200):
        def get_response(_request):
            return HttpResponse(status=status)

        middleware = RequestLoggingMiddleware(get_response)
        request = self.factory.get("/some/path/")
        request.user = AnonymousUser()
        return middleware(request)

    @override_settings(ENABLE_REQUEST_LOGGING=True)
    def test_logs_request_when_enabled(self):
        with self.assertLogs(_LOGGER, level="INFO") as cm:
            response = self._run(status=200)

        self.assertEqual(response.status_code, 200)
        record = cm.records[0]
        self.assertEqual(record.getMessage(), "request")
        self.assertEqual(record.method, "GET")
        self.assertEqual(record.path, "/some/path/")
        self.assertEqual(record.status, 200)
        self.assertIsNone(record.user_id)
        self.assertIsInstance(record.ms, int)

    @override_settings(ENABLE_REQUEST_LOGGING=False)
    def test_silent_when_disabled(self):
        with self.assertNoLogs(_LOGGER, level="INFO"):
            self._run()

    def test_does_not_swallow_response(self):
        with override_settings(ENABLE_REQUEST_LOGGING=True):
            response = self._run(status=404)
        self.assertEqual(response.status_code, 404)
