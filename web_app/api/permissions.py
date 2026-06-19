from django.conf import settings as django_settings
from rest_framework.permissions import BasePermission


class IsPrintAgent(BasePermission):
    """店內列印代理：以 X-Print-Token header 比對 settings.PRINT_AGENT_TOKEN。"""

    def has_permission(self, request, view):
        token = getattr(django_settings, "PRINT_AGENT_TOKEN", "")
        provided = request.headers.get("X-Print-Token", "")
        return bool(token) and provided == token


class IsEmployee(BasePermission):
    """員工或管理員（identity in A, E）"""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "identity", None) in ("A", "E")
        )


class IsAdmin(BasePermission):
    """管理員（identity == A）"""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "identity", None) == "A"
        )


class IsCustomer(BasePermission):
    """一般顧客（identity == C，排除訪客與員工）"""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "identity", None) == "C"
        )
