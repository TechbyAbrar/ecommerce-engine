from collections.abc import AsyncGenerator

from app.core.database import AsyncSession, AsyncSessionLocal


async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
