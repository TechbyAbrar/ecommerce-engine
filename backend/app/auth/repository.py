#app/auth/repository.py
"""
Data access layer for the auth domain. Keeps raw SQLAlchemy queries out of
the service layer so business logic stays storage-agnostic.
"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshSession, User
from app.auth.schemas import UserCreate
from app.common.utils import utc_now
from app.core.security import hash_password


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user_in: UserCreate) -> User:
        user = User(
            email=user_in.email,
            hashed_password=hash_password(user_in.password),
            full_name=user_in.full_name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password_hash(self, user_id: uuid.UUID, hashed_password: str) -> None:
        await self.db.execute(
            update(User).where(User.id == user_id).values(hashed_password=hashed_password)
        )
        await self.db.commit()

    async def record_login_failure(self, user: User, max_attempts: int, lock_minutes: int) -> None:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= max_attempts:
            user.locked_until = utc_now() + timedelta(minutes=lock_minutes)
            user.failed_login_attempts = 0
        await self.db.commit()

    async def clear_login_failures(self, user: User) -> None:
        if user.failed_login_attempts or user.locked_until:
            user.failed_login_attempts = 0
            user.locked_until = None
            await self.db.commit()

    async def mark_email_verified(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(User).where(User.id == user_id).values(is_verified=True)
        )
        await self.db.commit()

    async def create_refresh_session(
        self, user_id: uuid.UUID, jti: str, expires_at: datetime
    ) -> None:
        self.db.add(RefreshSession(user_id=user_id, jti=jti, expires_at=expires_at))
        await self.db.commit()

    async def rotate_refresh_session(
        self, user_id: uuid.UUID, current_jti: str, new_jti: str, expires_at: datetime
    ) -> bool:
        result = await self.db.execute(
            update(RefreshSession)
            .where(
                RefreshSession.user_id == user_id,
                RefreshSession.jti == current_jti,
                RefreshSession.revoked_at.is_(None),
                RefreshSession.expires_at > utc_now(),
            )
            .values(revoked_at=utc_now())
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            await self.db.rollback()
            return False
        self.db.add(RefreshSession(user_id=user_id, jti=new_jti, expires_at=expires_at))
        await self.db.commit()
        return True

    async def revoke_refresh_session(self, user_id: uuid.UUID, jti: str) -> bool:
        result = await self.db.execute(
            update(RefreshSession)
            .where(
                RefreshSession.user_id == user_id,
                RefreshSession.jti == jti,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=utc_now())
            .execution_options(synchronize_session=False)
        )
        await self.db.commit()
        return result.rowcount == 1

    async def revoke_all_refresh_sessions(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(RefreshSession)
            .where(RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None))
            .values(revoked_at=utc_now())
            .execution_options(synchronize_session=False)
        )
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()
