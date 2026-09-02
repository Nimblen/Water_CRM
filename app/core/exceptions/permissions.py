from .base import AppException



class ForbiddenError(AppException):
    status_code = 403
    code = "FORBIDDEN"
    message = "Permission denied"


class AccessDeniedError(AppException):
    status_code = 403
    code = "ACCESS_DENIED"
    message = "Access denied"


class OrderAccessDeniedError(AppException):
    status_code = 403
    code = "ORDER_ACCESS_DENIED"
    message = "Order access denied"



class ExpenseAccessDeniedError(AppException):
    status_code = 403
    code = "EXPENSE_ACCESS_DENIED"
    message = "Expense access denied"