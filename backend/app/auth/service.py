#app/auth/service.py
"""
Business logic for the auth domain: registration, login, and token refresh.
Coordinates the repository (data access) and security (JWT/hashing) layers.
"""
import uuid
from datetime import timedelta

from celery.exceptions import CeleryError
from kombu.exceptions import OperationalError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import (
    AccountLockedException,
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
from app.auth.schemas import (
    ChangePasswordRequest,
    EmailVerificationRequest,
    PasswordResetRequest,
    Token,
    UserCreate,
    UserLogin,
)
from app.auth.security import create_access_token, create_refresh_token, decode_token
from app.auth.tasks import send_otp_email
from app.common.enums import OTPPurpose, TokenType, UserStatus
from app.common.utils import utc_now
from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import verify_and_update_password

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
        self.otp_service = OTPService(db)

    async def register(
        self, user_in: UserCreate, request_id: str | None = None, endpoint: str | None = None
    ) -> User:
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
        code = await self.otp_service.issue(user, OTPPurpose.EMAIL_VERIFICATION)
        self._queue_otp_email(user, code, OTPPurpose.EMAIL_VERIFICATION, request_id)
        logger.info(
            "user_registered",
            extra={
                "request_id": request_id,
                "endpoint": endpoint,
                "user_id": str(user.id),
                "email": user.email,
            },
        )
        return user

    async def authenticate(self, credentials: UserLogin) -> Token:
        user = await self.repository.get_by_email(credentials.email)
        if not user:
            raise InvalidCredentialsException()

        if user.locked_until and user.locked_until > utc_now():
            raise AccountLockedException()
        if user.locked_until:
            await self.repository.clear_login_failures(user)

        is_valid, updated_hash = verify_and_update_password(
            credentials.password, user.hashed_password
        )
        if not is_valid:
            await self.repository.record_login_failure(
                user, settings.MAX_LOGIN_ATTEMPTS, settings.ACCOUNT_LOCK_MINUTES
            )
            if user.locked_until and user.locked_until > utc_now():
                raise AccountLockedException()
            raise InvalidCredentialsException()

        if user.status != UserStatus.ACTIVE:
            raise InactiveUserException()
        if not user.is_verified:
            raise EmailNotVerifiedException()

        if updated_hash:
            await self.repository.update_password_hash(user.id, updated_hash)

        await self.repository.clear_login_failures(user)

        return await self._issue_tokens(user.id)

    async def verify_email(self, payload: EmailVerificationRequest) -> None:
        user = await self.repository.get_by_email(payload.email)
        if not user:
            raise InvalidOTPException()
        await self.otp_service.verify(user.id, OTPPurpose.EMAIL_VERIFICATION, payload.code)
        await self.repository.mark_email_verified(user.id)
        await self.repository.clear_login_failures(user)

    async def resend_email_verification(self, email: str, request_id: str | None = None) -> None:
        user = await self.repository.get_by_email(email)
        if not user or user.is_verified:
            return
        code = await self.otp_service.issue(user, OTPPurpose.EMAIL_VERIFICATION)
        self._queue_otp_email(user, code, OTPPurpose.EMAIL_VERIFICATION, request_id)

    @staticmethod
    def _queue_otp_email(
        user: User, code: str, purpose: OTPPurpose, request_id: str | None
    ) -> None:
        """Publish after the database commit; a broker outage must not fail registration."""
        try:
            send_otp_email.delay(
                recipient=user.email,
                code=code,
                purpose=purpose.value,
                user_id=str(user.id),
                request_id=request_id,
            )
        except (CeleryError, OperationalError, OSError) as exc:
            logger.exception(
                "email_queue_failed",
                extra={
                    "request_id": request_id,
                    "user_id": str(user.id),
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                },
            )

    async def forgot_password(self, email: str, request_id: str | None = None) -> None:
        """Queue a reset OTP without revealing whether an email is registered."""
        user = await self.repository.get_by_email(email)
        if not user or user.status != UserStatus.ACTIVE:
            return
        code = await self.otp_service.issue(user, OTPPurpose.PASSWORD_RESET)
        self._queue_otp_email(user, code, OTPPurpose.PASSWORD_RESET, request_id)

    async def verify_password_reset_otp(self, payload: EmailVerificationRequest) -> None:
        user = await self.repository.get_by_email(payload.email)
        if not user:
            raise InvalidOTPException()
        await self.otp_service.verify(
            user.id, OTPPurpose.PASSWORD_RESET, payload.code, consume=False
        )

    async def reset_password(self, payload: PasswordResetRequest) -> None:
        user = await self.repository.get_by_email(payload.email)
        if not user:
            raise InvalidOTPException()
        await self.otp_service.verify(user.id, OTPPurpose.PASSWORD_RESET, payload.code)
        await self.repository.update_password_hash(user.id, self._hash_password(payload.new_password))
        await self.repository.revoke_all_refresh_sessions(user.id)

    async def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        is_valid, _ = verify_and_update_password(payload.current_password, user.hashed_password)
        if not is_valid:
            raise InvalidCredentialsException("Current password is incorrect")
        await self.repository.update_password_hash(user.id, self._hash_password(payload.new_password))
        await self.repository.revoke_all_refresh_sessions(user.id)

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
        refresh_expires_at = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        if current_refresh_jti is None:
            await self.repository.create_refresh_session(user_id, refresh_jti, refresh_expires_at)
        else:
            updated = await self.repository.rotate_refresh_session(
                user_id, current_refresh_jti, refresh_jti, refresh_expires_at
            )
            if not updated:
                raise InvalidTokenException("Refresh token has already been used or revoked")
        return Token(
            access_token=create_access_token(str(user_id)),
            refresh_token=create_refresh_token(str(user_id), refresh_jti),
        )

    async def logout(self, refresh_token: str) -> None:
        token_data = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        try:
            user_id = uuid.UUID(token_data.sub)
        except (TypeError, ValueError):
            raise InvalidTokenException()
        if not token_data.jti or not await self.repository.revoke_refresh_session(user_id, token_data.jti):
            raise InvalidTokenException("Refresh token has already been used or revoked")

    async def logout_all(self, user: User) -> None:
        await self.repository.revoke_all_refresh_sessions(user.id)

    @staticmethod
    def _hash_password(password: str) -> str:
        from app.core.security import hash_password

        return hash_password(password)
