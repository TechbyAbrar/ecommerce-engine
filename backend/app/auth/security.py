#app/auth/security.py
"""
JWT-specific security logic for the auth domain: creating and decoding
access/refresh tokens. Password hashing (domain-agnostic) lives in
app.core.security instead.
"""
from datetime import timedelta

from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import ValidationError

from app.auth.exceptions import InvalidTokenException, TokenExpiredException
from app.auth.schemas import TokenPayload
from app.common.enums import TokenType
from app.common.utils import utc_now
from app.core.config import settings


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    token_id: str | None = None,
) -> str:
    expire = utc_now() + expires_delta
    to_encode = {"sub": subject, "exp": expire, "type": token_type.value}
    if token_id is not None:
        to_encode["jti"] = token_id
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str) -> str:
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, TokenType.ACCESS, expires_delta)


def create_refresh_token(subject: str, token_id: str) -> str:
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(subject, TokenType.REFRESH, expires_delta, token_id)


def decode_token(token: str, expected_type: TokenType) -> TokenPayload:
    """Decode a JWT and validate its type. Raises auth-domain exceptions on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise TokenExpiredException()
    except JWTError:
        raise InvalidTokenException()

    try:
        token_data = TokenPayload(**payload)
    except ValidationError as exc:
        raise InvalidTokenException() from exc
    if token_data.type != expected_type.value:
        raise InvalidTokenException(f"Expected a {expected_type.value} token")
    return token_data
