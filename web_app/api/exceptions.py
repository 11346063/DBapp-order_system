from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from web_app.services.exceptions import (
    NotFoundError,
    PermissionBusinessError,
    ServiceError,
    ValidationServiceError,
)

_SERVICE_STATUS_MAP = {
    ValidationServiceError: status.HTTP_400_BAD_REQUEST,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    PermissionBusinessError: status.HTTP_403_FORBIDDEN,
}


def _error_response(message, http_status, errors=None):
    body = {"status": "error", "message": message}
    if errors:
        body["errors"] = errors
    return Response(body, status=http_status)


def custom_exception_handler(exc, context):
    # --- DRF / Django 標準例外 ---
    if isinstance(exc, ValidationError):
        errors = exc.detail if isinstance(exc.detail, dict) else {}
        if errors:
            first_field_msgs = next(iter(errors.values()))
            first_msg = first_field_msgs[0] if first_field_msgs else "資料驗證失敗"
        elif isinstance(exc.detail, list) and exc.detail:
            first_msg = exc.detail[0]
        else:
            first_msg = "資料驗證失敗"
        return _error_response(
            str(first_msg),
            status.HTTP_400_BAD_REQUEST,
            errors={k: [str(m) for m in v] for k, v in errors.items()}
            if errors
            else None,
        )

    if isinstance(exc, (NotAuthenticated,)):
        return _error_response("請先登入", status.HTTP_401_UNAUTHORIZED)

    if isinstance(exc, PermissionDenied):
        return _error_response(str(exc.detail), status.HTTP_403_FORBIDDEN)

    if isinstance(exc, (Http404, NotFound)):
        return _error_response("找不到指定資源", status.HTTP_404_NOT_FOUND)

    # --- Service layer 例外 ---
    if isinstance(exc, ServiceError):
        http_status = _SERVICE_STATUS_MAP.get(type(exc), exc.status_code)
        return _error_response(exc.message, http_status)

    # --- 其餘例外交給 DRF 預設處理 ---
    return drf_exception_handler(exc, context)
