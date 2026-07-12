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
