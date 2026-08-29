from .base import AppException






class ConflictError(AppException):
    status_code = 409
    code = "CONFLICT"
    message = "Conflict occurred"


class PhoneAlreadyExistsError(ConflictError):
    code = "PHONE_ALREADY_EXISTS"
    message = "Phone already exists"

class CustomerPhoneAlreadyExistsError(ConflictError):
    code = "CUSTOMER_PHONE_ALREADY_EXISTS"
    message = "Customer phone already exists"


class UserAlreadyExistsError(ConflictError):
    code = "USER_ALREADY_EXISTS"
    message = "User already exists"


class UserAlreadyInactiveError(ConflictError):
    code = "USER_ALREADY_INACTIVE"
    message = "User already inactive"



class InvalidDeliveryStatusError(ConflictError):
    code = "INVALID_DELIVERY_STATUS"
    message = "Invalid delivery status"


class RouteAlreadyStartedError(ConflictError):
    code = "ROUTE_ALREADY_STARTED"
    message = "Route already started"
    detail = "Нельзя сменить водителя — маршрут уже в работе"


class RouteAlreadyCompletedError(ConflictError):
    code = "ROUTE_ALREADY_COMPLETED"
    message = "Route already completed"



class CustomerAlreadyInactiveError(ConflictError):
    code = "CUSTOMER_ALREADY_INACTIVE"
    message = "Customer already inactive"

class CustomerAlreadyActiveError(ConflictError):
    code = "CUSTOMER_ALREADY_ACTIVE"
    message = "Customer already active"


class PasswordNotSetError(ConflictError):
    code = "PASSWORD_NOT_SET"
    message = "Password not set"



class BothBalancesSetError(ConflictError):
    code = "BOTH_BALANCES_SET"
    message = "Both balances set"