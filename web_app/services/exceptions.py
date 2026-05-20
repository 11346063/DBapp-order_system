class ServiceError(Exception):
    """Base exception for service-layer domain errors."""

    status_code = 400

    def __init__(self, message="操作失敗", *, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationServiceError(ServiceError):
    pass


class NotFoundError(ServiceError):
    status_code = 404


class PermissionBusinessError(ServiceError):
    status_code = 403


class EmptyCartError(ServiceError):
    pass
