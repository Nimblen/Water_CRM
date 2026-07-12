class AppException(Exception):
    status_code = 400
    code = "APPLICATION_ERROR"
    message = "Application error"

    def __init__(self, details=None):
        self.details = details