#app/auth/dependencies.py
"""
Auth-domain-specific FastAPI dependencies, e.g. extracting & validating the
current user from a bearer token.
"""
import uuid

from collections.abc import Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import InactiveUserException, InvalidTokenException
from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.security import decode_token
from app.common.enums import TokenType, UserRole, UserStatus
from app.core.exceptions import ForbiddenException
from app.core.dependencies import get_db

bearer_scheme = HTTPBearer()


async def get_current_user(
    request: Request,
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

    request.state.user_id = str(user.id)
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.status != UserStatus.ACTIVE:
        raise InactiveUserException()
    return current_user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Create a dependency that restricts an endpoint to one or more roles."""
    async def role_dependency(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in roles:
            raise ForbiddenException("You do not have permission to perform this action")
        return current_user

    return role_dependency
