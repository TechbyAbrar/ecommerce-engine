#app/core/exceptions.py
"""
Base application exceptions and their FastAPI exception handlers.

Domain-specific exceptions (e.g. auth) subclass `AppException` and live in
their own module (see app/auth/exceptions.py) but are registered centrally
here via `register_exception_handlers`.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


def _request_context(request: Request) -> dict[str, str | int]:
    """Return request metadata that is safe and useful for structured logs."""
    context: dict[str, str | int] = {
        "method": request.method,
        "path": request.url.path,
    }
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        context["request_id"] = request_id
    return context


class AppException(Exception):
    """Base class for all custom, handled application exceptions."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "APP_ERROR"

    def __init__(self, message: str = "An application error occurred"):
        self.message = message
        super().__init__(message)


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"


class ConflictException(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"


class UnauthorizedException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHORIZED"


class ForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        "business_exception",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            **_request_context(request),
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error_code": exc.error_code, "message": exc.message},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    context = _request_context(request)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        context["user_id"] = user_id
    logger.exception(
        "unhandled_exception",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            **context,
        },
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
