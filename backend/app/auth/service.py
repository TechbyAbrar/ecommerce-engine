#app/auth/service.py
"""
Business logic for the auth domain: registration, login, and token refresh.
Coordinates the repository (data access) and security (JWT/hashing) layers.
"""
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import (
    EmailNotVerifiedException,
    InactiveUserException,
    InvalidCredentialsException,
    InvalidOTPException,
    InvalidTokenException,
    UserAlreadyExistsException,
)
from app.auth.models import User
from app.auth.otp_service import OTPService
from app.auth.repository import UserRepository
from app.auth.schemas import EmailVerificationRequest, Token, UserCreate, UserLogin
from app.auth.security import create_access_token, create_refresh_token, decode_token
from app.common.enums import OTPPurpose, TokenType, UserStatus
from app.core.security import verify_and_update_password


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
        self.otp_service = OTPService(db)

    async def register(self, user_in: UserCreate) -> User:
        existing_user = await self.repository.get_by_email(user_in.email)
        if existing_user:
            raise UserAlreadyExistsException()
        try:
            user = await self.repository.create(user_in)
        except IntegrityError:
            await self.repository.rollback()
            if await self.repository.get_by_email(user_in.email):
                raise UserAlreadyExistsException()
            raise
        await self.otp_service.issue(user, OTPPurpose.EMAIL_VERIFICATION)
        return user

    async def authenticate(self, credentials: UserLogin) -> Token:
        user = await self.repository.get_by_email(credentials.email)
        if not user:
            raise InvalidCredentialsException()

        is_valid, updated_hash = verify_and_update_password(
            credentials.password, user.hashed_password
        )
        if not is_valid:
            raise InvalidCredentialsException()

        if user.status != UserStatus.ACTIVE:
            raise InactiveUserException()
        if not user.is_verified:
            raise EmailNotVerifiedException()

        if updated_hash:
            await self.repository.update_password_hash(user.id, updated_hash)

        return await self._issue_tokens(user.id)

    async def verify_email(self, payload: EmailVerificationRequest) -> None:
        user = await self.repository.get_by_email(payload.email)
        if not user:
            raise InvalidOTPException()
        await self.otp_service.verify(user.id, OTPPurpose.EMAIL_VERIFICATION, payload.code)
        await self.repository.mark_email_verified(user.id)

    async def resend_email_verification(self, email: str) -> None:
        user = await self.repository.get_by_email(email)
        if not user or user.is_verified:
            return
        await self.otp_service.issue(user, OTPPurpose.EMAIL_VERIFICATION)

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
