from .base import AppException


class InvalidCredentialsError(AppException):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    message = "Invalid phone or password"


class UnauthorizedError(AppException):
    status_code = 401
    code = "UNAUTHORIZED"
    message = "Authentication required"


class InvalidTokenError(AppException):
    status_code = 401
    code = "INVALID_TOKEN"
    message = "Invalid token"


class TokenExpiredError(AppException):
    status_code = 401
    code = "TOKEN_EXPIRED"
    message = "Token expired"


class RefreshTokenExpiredError(AppException):
    status_code = 401
    code = "REFRESH_TOKEN_EXPIRED"
    message = "Refresh token expired"


class RefreshTokenRevokedError(AppException):
    status_code = 401
    code = "REFRESH_TOKEN_REVOKED"
    message = "Refresh token revoked"