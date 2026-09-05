from .base import AppException





class InvalidUpdateFieldsError(AppException):
    status_code = 400
    code = "INVALID_UPDATE_FIELDS"
    message = "Invalid update fields"


class MoveDateInPastError(AppException):
    status_code = 422
    code = "DATE_IN_PAST"
    message = "Date in the past"



class BulkPriceRequiredError(AppException):
    status_code = 422
    code = "BULK_PRICE_REQUIRED"
    message = "Bulk price is required"

class DeliveryQuantityRequiredError(AppException):
    status_code = 422
    code = "DELIVERY_QUANTITY_REQUIRED"
    message = "Delivery quantity is required"


class PickupQuantityRequiredError(AppException):
    status_code = 422
    code = "PICKUP_QUANTITY_REQUIRED"
    message = "Pickup quantity is required"

class InvalidDamagedCountError(AppException):
    status_code = 422
    code = "INVALID_DAMAGED_COUNT"
    message = "Invalid damaged count"



class PaymentAmountInvalidError(AppException):
    status_code = 422
    code = "INVALID_PAYMENT_AMOUNT"
    message = "Invalid payment amount"