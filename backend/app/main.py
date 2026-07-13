import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import models as auth_models  # noqa: F401 - registers ORM metadata
from app.auth.otp_service import OTPService
from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging


async def _cleanup_expired_otps() -> None:
    """Keep short-lived OTP records from accumulating between deployments."""
    while True:
        async with AsyncSessionLocal() as session:
            await OTPService(session).cleanup_expired()
        await asyncio.sleep(60 * 60)


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    await init_db()
    cleanup_task = asyncio.create_task(_cleanup_expired_otps())
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
