"""Low-overhead, structured application and HTTP access logging."""
import json
import logging
import sys
from datetime import datetime, timezone
from logging.config import dictConfig
from pathlib import Path
from typing import Any

from app.core.config import settings

_ACCESS_LOG_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
)

_APPLICATION_LOG_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "error_code",
    "exception_type",
    "exception_message",
    "user_id",
    "email",
    "endpoint",
)


class JsonFormatter(logging.Formatter):
    """Emit a small, allow-listed JSON record to avoid accidental secret logging."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        if record.name == "app.access":
            payload = {"timestamp": timestamp}
            for field in _ACCESS_LOG_FIELDS:
                value = getattr(record, field, None)
                if value is not None:
                    payload[field] = value
            return json.dumps(payload, separators=(",", ":"), default=str)

        payload: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for field in _APPLICATION_LOG_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["module"] = record.module
            payload["filename"] = record.filename
            payload["function"] = record.funcName
            payload["line_number"] = record.lineno
        return json.dumps(payload, separators=(",", ":"), default=str)


def setup_logging() -> None:
    """Configure once at startup; delayed file handlers keep idle resource use low."""
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_level = (settings.LOG_LEVEL or ("DEBUG" if settings.DEBUG else "INFO")).upper()

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "json",
                "stream": sys.stdout,
            },
            "application_file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": log_level,
                "formatter": "json",
                "filename": str(log_dir / "application.log"),
                "when": "midnight",
                "backupCount": settings.LOG_RETENTION_DAYS,
                "encoding": "utf-8",
                "delay": True,
            },
            "access_file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(log_dir / "access.log"),
                "when": "midnight",
                "backupCount": settings.LOG_RETENTION_DAYS,
                "encoding": "utf-8",
                "delay": True,
            },
        },
        "root": {"level": "WARNING", "handlers": ["console"]},
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": ["console", "application_file"],
                "propagate": False,
            },
            "app.access": {
                "level": "INFO",
                "handlers": ["access_file"],
                "propagate": False,
            },
            "uvicorn.access": {"level": "WARNING", "handlers": [], "propagate": False},
            "uvicorn.error": {
                "level": log_level,
                "handlers": ["console", "application_file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {"level": "WARNING", "handlers": [], "propagate": False},
        },
    }
    dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def get_access_logger() -> logging.Logger:
    return logging.getLogger("app.access")
