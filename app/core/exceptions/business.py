from .base import AppException


class BusinessError(AppException):
    status_code = 400
    code = "BUSINESS_ERROR"
    message = "Business rule violation"




class ContractClosedError(BusinessError):
    code = "CONTRACT_CLOSED"
    message = "Contract already closed"


class ContractCancelledError(BusinessError):
    code = "CONTRACT_CANCELLED"
    message = "Contract already cancelled"


class DriverBusyError(BusinessError):
    code = "DRIVER_BUSY"
    message = "Driver is busy"