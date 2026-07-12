#app/auth/dependencies.py
"""
Auth-domain-specific FastAPI dependencies, e.g. extracting & validating the
current user from a bearer token.
"""
import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import InactiveUserException, InvalidTokenException
from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.security import decode_token
from app.common.enums import TokenType, UserStatus
from app.core.dependencies import get_db

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token_data = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)

    try:
        user_id = uuid.UUID(token_data.sub)
    except (TypeError, ValueError):
        raise InvalidTokenException()

    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        raise InvalidTokenException()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.status != UserStatus.ACTIVE:
        raise InactiveUserException()
    return current_user
