#app/core/logging.py
"""
Centralized logging configuration.

Call `setup_logging()` once on application startup (see app/main.py).
"""
import logging
import sys
from logging.config import dictConfig

from app.core.config import settings

LOG_LEVEL = "DEBUG" if settings.DEBUG else "INFO"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": sys.stdout,
        },
    },
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["console"],
    },
    "loggers": {
        "uvicorn": {"level": LOG_LEVEL, "handlers": ["console"], "propagate": False},
        "sqlalchemy.engine": {"level": "WARNING", "handlers": ["console"], "propagate": False},
    },
}


def setup_logging() -> None:
    dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """Convenience accessor, e.g. logger = get_logger(__name__)."""
    return logging.getLogger(name)
