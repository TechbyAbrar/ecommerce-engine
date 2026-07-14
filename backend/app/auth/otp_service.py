"""Reusable, database-backed OTP issuance, verification, and cleanup."""
import hashlib
import hmac
import secrets
from datetime import timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import InvalidOTPException, OTPRateLimitException
from app.auth.models import OTP, User
from app.common.enums import OTPPurpose
from app.common.utils import utc_now
from app.core.config import settings


class OTPService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _hash(code: str) -> str:
        """Key the OTP hash so a database leak cannot be brute-forced offline."""
        return hmac.new(
            settings.SECRET_KEY.encode("utf-8"), code.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _generate_code() -> str:
        upper_bound = 10 ** settings.OTP_LENGTH
        return f"{secrets.randbelow(upper_bound):0{settings.OTP_LENGTH}d}"

    async def issue(self, user: User, purpose: OTPPurpose) -> str:
        now = utc_now()
        # Serialize issuance per user so concurrent resend requests cannot create
        # two active OTPs for the same purpose.
        await self.db.execute(select(User.id).where(User.id == user.id).with_for_update())
        latest = await self.db.scalar(
            select(OTP)
            .where(OTP.user_id == user.id, OTP.purpose == purpose)
            .order_by(OTP.created_at.desc())
            .limit(1)
        )
        if latest and (now - latest.created_at).total_seconds() < settings.OTP_RESEND_COOLDOWN_SECONDS:
            raise OTPRateLimitException()

        # Invalidate any previous code for this purpose before creating the new one.
        await self.db.execute(
            update(OTP)
            .where(OTP.user_id == user.id, OTP.purpose == purpose, OTP.used.is_(False))
            .values(used=True)
        )
        code = self._generate_code()
        otp = OTP(
            user_id=user.id,
            purpose=purpose,
            otp_hash=self._hash(code),
            expires_at=now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        )
        self.db.add(otp)
        await self.db.commit()
        return code

    async def verify(
        self, user_id, purpose: OTPPurpose, code: str, consume: bool = True
    ) -> None:
        now = utc_now()
        otp = await self.db.scalar(
            select(OTP)
            .where(OTP.user_id == user_id, OTP.purpose == purpose, OTP.used.is_(False))
            .order_by(OTP.created_at.desc())
            .with_for_update()
        )
        if otp is None:
            raise InvalidOTPException()

        if otp.expires_at <= now or otp.attempts >= settings.OTP_MAX_ATTEMPTS:
            otp.used = True
            await self.db.commit()
            raise InvalidOTPException()

        otp.attempts += 1
        if not hmac.compare_digest(otp.otp_hash, self._hash(code)):
            if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
                otp.used = True
            await self.db.commit()
            raise InvalidOTPException()

        if consume:
            otp.used = True
        await self.db.commit()

    async def cleanup_expired(self) -> int:
        """Delete expired OTPs; invoke this from a scheduled worker in production."""
        result = await self.db.execute(delete(OTP).where(OTP.expires_at < utc_now()))
        await self.db.commit()
        return result.rowcount or 0
