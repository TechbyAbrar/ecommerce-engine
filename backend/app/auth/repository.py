#app/auth/repository.py
"""
Data access layer for the auth domain. Keeps raw SQLAlchemy queries out of
the service layer so business logic stays storage-agnostic.
"""
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import UserCreate
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

    async def replace_refresh_token_jti(
        self, user_id: uuid.UUID, new_jti: str, current_jti: str | None = None
    ) -> bool:
        statement = update(User).where(User.id == user_id)
        if current_jti is not None:
            statement = statement.where(User.refresh_token_jti == current_jti)

        result = await self.db.execute(
            statement.values(refresh_token_jti=new_jti).execution_options(synchronize_session=False)
        )
        await self.db.commit()
        return result.rowcount == 1

    async def rollback(self) -> None:
        await self.db.rollback()
