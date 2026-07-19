from .base import AppException





class InvalidUpdateFieldsError(AppException):
    status_code = 400
    code = "INVALID_UPDATE_FIELDS"
    message = "Invalid update fields"