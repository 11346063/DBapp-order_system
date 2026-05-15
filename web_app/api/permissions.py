from rest_framework.permissions import BasePermission


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
