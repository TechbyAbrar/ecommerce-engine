#app/core/database.py
"""
Async SQLAlchemy engine, session factory, and declarative base.
"""
import ssl
from uuid import uuid4

ssl_context = ssl.create_default_context()

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    poolclass=NullPool,
    future=True,
    connect_args={
        "ssl": ssl_context,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


async def init_db() -> None:
    """Create tables on startup (use Alembic migrations in production instead)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
