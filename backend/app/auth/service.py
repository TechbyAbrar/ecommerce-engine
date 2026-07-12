#app/auth/service.py
"""
Business logic for the auth domain: registration, login, and token refresh.
Coordinates the repository (data access) and security (JWT/hashing) layers.
"""
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import (
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
    UserAlreadyExistsException,
)
from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.schemas import Token, UserCreate, UserLogin
from app.auth.security import create_access_token, create_refresh_token, decode_token
from app.common.enums import TokenType, UserStatus
from app.core.security import verify_password


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def register(self, user_in: UserCreate) -> User:
        existing_user = await self.repository.get_by_email(user_in.email)
        if existing_user:
            raise UserAlreadyExistsException()
        try:
            return await self.repository.create(user_in)
        except IntegrityError:
            await self.repository.rollback()
            if await self.repository.get_by_email(user_in.email):
                raise UserAlreadyExistsException()
            raise

    async def authenticate(self, credentials: UserLogin) -> Token:
        user = await self.repository.get_by_email(credentials.email)
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise InvalidCredentialsException()

        if user.status != UserStatus.ACTIVE:
            raise InactiveUserException()

        return await self._issue_tokens(user.id)

    async def refresh(self, refresh_token: str) -> Token:
        token_data = decode_token(refresh_token, expected_type=TokenType.REFRESH)

        try:
            user_id = uuid.UUID(token_data.sub)
        except (TypeError, ValueError):
            raise InvalidTokenException()

        user = await self.repository.get_by_id(user_id)
        if not user or user.status != UserStatus.ACTIVE or not token_data.jti:
            raise InvalidTokenException()

        return await self._issue_tokens(user.id, current_refresh_jti=token_data.jti)

    async def _issue_tokens(
        self, user_id: uuid.UUID, current_refresh_jti: str | None = None
    ) -> Token:
        refresh_jti = str(uuid.uuid4())
        updated = await self.repository.replace_refresh_token_jti(
            user_id, refresh_jti, current_refresh_jti
        )
        if not updated:
            raise InvalidTokenException("Refresh token has already been used or revoked")
        return Token(
            access_token=create_access_token(str(user_id)),
            refresh_token=create_refresh_token(str(user_id), refresh_jti),
        )
