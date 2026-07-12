#app/core/dependencies.py
"""
Shared, cross-cutting FastAPI dependencies.

Domain-specific dependencies (e.g. get_current_user) live in their own
module, such as app/auth/dependencies.py.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session and guarantee it's closed after the request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
