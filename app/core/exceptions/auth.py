from .base import AppException



class AuthenticationError(AppException):
    status_code = 401
    code = "AUTHENTICATION_ERROR"
    message = "Authentication error"


class InvalidCredentialsError(AuthenticationError):
    code = "INVALID_CREDENTIALS"
    message = "Invalid phone or password"


class UnauthorizedError(AuthenticationError):
    code = "UNAUTHORIZED"
    message = "Authentication required"


class InvalidTokenError(AuthenticationError):
    code = "INVALID_TOKEN"
    message = "Invalid token"


class TokenExpiredError(AuthenticationError):
    code = "TOKEN_EXPIRED"
    message = "Token expired"


class RefreshTokenExpiredError(AuthenticationError):
    code = "REFRESH_TOKEN_EXPIRED"
    message = "Refresh token expired"


class RefreshTokenRevokedError(AuthenticationError):
    code = "REFRESH_TOKEN_REVOKED"
    message = "Refresh token revoked"


class TokenTypeError(AuthenticationError):
    code = "INVALID_TOKEN_TYPE"
    message = "Invalid token type"


class PasswordIncorrectError(AuthenticationError):
    code = "PASSWORD_INCORRECT"
    message = "Password incorrect"