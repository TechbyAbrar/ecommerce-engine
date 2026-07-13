#app/common/enums.py
"""
Enums shared across multiple domains.
"""
from enum import Enum

class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class OTPPurpose(str, Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
