from .base import AppException



class ForbiddenError(AppException):
    status_code = 403
    code = "FORBIDDEN"
    message = "Permission denied"


class AccessDeniedError(AppException):
    status_code = 403
    code = "ACCESS_DENIED"
    message = "Access denied"