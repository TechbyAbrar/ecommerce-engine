#app/auth/exceptions.py
"""
Auth-domain-specific exceptions, subclassing the shared AppException types.
"""
from fastapi import status

from app.core.exceptions import AppException, ConflictException, UnauthorizedException


class UserAlreadyExistsException(ConflictException):
    error_code = "USER_ALREADY_EXISTS"

    def __init__(self, message: str = "A user with this email already exists"):
        super().__init__(message)


class InvalidCredentialsException(UnauthorizedException):
    error_code = "INVALID_CREDENTIALS"

    def __init__(self, message: str = "Incorrect email or password"):
        super().__init__(message)


class InvalidTokenException(UnauthorizedException):
    error_code = "INVALID_TOKEN"

    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(message)


class TokenExpiredException(UnauthorizedException):
    error_code = "TOKEN_EXPIRED"

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InactiveUserException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "INACTIVE_USER"

    def __init__(self, message: str = "This user account is inactive"):
        super().__init__(message)


class UserNotFoundException(UnauthorizedException):
    error_code = "USER_NOT_FOUND"

    def __init__(self, message: str = "User was not found"):
        super().__init__(message)


class AccountLockedException(AppException):
    status_code = status.HTTP_423_LOCKED
    error_code = "ACCOUNT_LOCKED"

    def __init__(self, message: str = "Too many failed sign-in attempts. Try again later"):
        super().__init__(message)


class EmailNotVerifiedException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "EMAIL_NOT_VERIFIED"

    def __init__(self, message: str = "Verify your email address before signing in"):
        super().__init__(message)


class InvalidOTPException(AppException):
    error_code = "INVALID_OTP"

    def __init__(self, message: str = "The code is invalid, expired, or has already been used"):
        super().__init__(message)


class OTPRateLimitException(AppException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "OTP_RATE_LIMITED"

    def __init__(self, message: str = "Please wait before requesting another code"):
        super().__init__(message)
