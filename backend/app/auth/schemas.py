#app/auth/schemas.py
"""
Pydantic schemas for the auth domain (request bodies & response shapes).
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.common.enums import UserRole, UserStatus
from app.common.validators import normalize_email, validate_password_strength
from app.core.config import settings


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return normalize_email(v)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return normalize_email(v)


class EmailVerificationRequest(BaseModel):
    email: EmailStr
    code: str

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return normalize_email(v)

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        if not v.isascii() or not v.isdigit() or len(v) != settings.OTP_LENGTH:
            raise ValueError("Invalid verification code")
        return v


class ResendVerificationRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return normalize_email(v)


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: UserRole
    status: UserStatus
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str  # user id
    exp: int
    type: str  # "access" | "refresh"
    jti: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
