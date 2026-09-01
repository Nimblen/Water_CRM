from .base import AppException





class InvalidUpdateFieldsError(AppException):
    status_code = 400
    code = "INVALID_UPDATE_FIELDS"
    message = "Invalid update fields"


class MoveDateInPastError(AppException):
    status_code = 422
    code = "DATE_IN_PAST"
    message = "Date in the past"