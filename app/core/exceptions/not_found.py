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


class RouteNotFoundError(NotFoundError):
    code = "ROUTE_NOT_FOUND"
    message = "Route not found"



class OrderNotFoundError(NotFoundError):
    code = "ORDER_NOT_FOUND"
    message = "Order not found"


class CustomerNotFoundError(NotFoundError):
    code = "CUSTOMER_NOT_FOUND"
    message = "Customer not found"