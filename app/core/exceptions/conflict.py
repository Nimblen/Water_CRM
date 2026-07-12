from .base import AppException






class ConflictError(AppException):
    status_code = 409
    code = "CONFLICT"
    message = "Conflict occurred"


class PhoneAlreadyExistsError(ConflictError):
    code = "PHONE_ALREADY_EXISTS"
    message = "Phone already exists"


class UserAlreadyExistsError(ConflictError):
    code = "USER_ALREADY_EXISTS"
    message = "User already exists"