#app/common/validators.py
import re

PASSWORD_MIN_LENGTH = 8
_UPPER_RE = re.compile(r"[A-Z]")
_LOWER_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"\d")
_SPECIAL_RE = re.compile(r"[!@#$%^&*(),.?\":{}|<>]")


def validate_password_strength(password: str) -> str:
    """
    Raise ValueError if the password doesn't meet minimum strength requirements.
    Intended for use inside a pydantic @field_validator.
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
    if not _UPPER_RE.search(password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not _LOWER_RE.search(password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not _DIGIT_RE.search(password):
        raise ValueError("Password must contain at least one digit")
    if not _SPECIAL_RE.search(password):
        raise ValueError("Password must contain at least one special character")
    return password


def normalize_email(email: str) -> str:
    return email.strip().lower()
