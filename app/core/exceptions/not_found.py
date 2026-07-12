from .base import AppException




class NotFoundError(AppException):
    status_code = 404
    code = "NOT_FOUND"
    message = "Resource not found"




class UserNotFoundError(NotFoundError):
    code = "USER_NOT_FOUND"
    message = "User not found"


class ContractNotFoundError(NotFoundError):
    code = "CONTRACT_NOT_FOUND"
    message = "Contract not found"


class DriverNotFoundError(NotFoundError):
    code = "DRIVER_NOT_FOUND"
    message = "Driver not found"