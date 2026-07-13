import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine  # CRITICAL for asyncpg
from dotenv import load_dotenv

from alembic import context

# Dynamically append the current working directory to the Python path
# This allows Alembic to find the 'app' module cleanly from the root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 1. Load environment variables from your local .env file
load_dotenv()

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 2. Pull the Neon DATABASE_URL dynamically from your environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing from your .env file!")

# Force Alembic to use your real Neon URL instead of the placeholder in alembic.ini
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------
# 3. LINK YOUR METADATA & IMPORT ALL MODERN SUBMODULES
# ---------------------------------------------------------------------
# Base holds the metadata registry where all tables register themselves
from app.core.database import Base  

# Explicitly import all domain models so Alembic's autogenerate 
# engine can discover them and construct your migrations accurately.
from app.auth import models as auth_models          # For OTP/Auth tables
from app.users import models as user_models          # For User tables
from app.categories import models as cat_models     # For Category tables
from app.products import models as prod_models      # For Product tables
from app.orders import models as order_models        # For Order tables
from app.payments import models as pay_models        # For Payment tables

# Target the combined metadata registry
target_metadata = Base.metadata
# ---------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Helper sync function to actually execute migrations."""
    context.configure(
        connection=connection, 
        target_metadata=target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    
    # Create the async engine required for postgresql+asyncpg connection to Neon
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # asyncpg requires running synchronous code wrapped inside a running event loop
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # 4. CRITICAL: Run the async execution wrapper loop instead of standard sync code
    asyncio.run(run_migrations_online())