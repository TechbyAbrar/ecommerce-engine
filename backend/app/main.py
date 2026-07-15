import asyncio
import time
import uuid
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import models as auth_models  # noqa: F401 - registers ORM metadata
from app.auth.otp_service import OTPService
from app.auth.router import router as auth_router
from app.categories.router import router as categories_router
from app.core.config import settings
from app.core import reference_models  # noqa: F401 - registers ORM metadata
from app.core.database import AsyncSessionLocal, init_db
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_access_logger, get_logger, setup_logging
from app.orders.router import router as orders_router
from app.payments.router import router as payments_router
from app.payments.webhook import router as payment_webhook_router
from app.products.router import router as products_router


async def _cleanup_expired_otps() -> None:
    """Keep short-lived OTP records from accumulating between deployments."""
    while True:
        async with AsyncSessionLocal() as session:
            await OTPService(session).cleanup_expired()
        await asyncio.sleep(60 * 60)


access_logger = get_access_logger()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    if settings.ENVIRONMENT.lower() != "production":
        await init_db()
    logger.info("application_started")
    cleanup_task = asyncio.create_task(_cleanup_expired_otps())
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task
        logger.info("application_stopped")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_access(request, call_next):
    """Log method, path, status, and duration only—never bodies, queries, or headers."""
    request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        access_logger.error(
            "http_request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        raise

    response.headers["X-Request-ID"] = request_id
    access_logger.info(
        "http_request_completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )
    return response


register_exception_handlers(app)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(categories_router, prefix=settings.API_V1_PREFIX)
app.include_router(products_router, prefix=settings.API_V1_PREFIX)
app.include_router(orders_router, prefix=settings.API_V1_PREFIX)
app.include_router(payments_router, prefix=settings.API_V1_PREFIX)
app.include_router(payment_webhook_router, prefix=settings.API_V1_PREFIX)
