"""Celery configuration shared by API processes and workers."""
from celery import Celery
from celery.signals import worker_process_init

from app.core.config import settings
from app.core.logging import setup_logging

celery_app = Celery(
    "ecommerce_engine",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.update(
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
)
celery_app.autodiscover_tasks(["app.auth"])


@worker_process_init.connect
def configure_worker_logging(**_: object) -> None:
    """Apply the application's JSON logging in each Celery worker process."""
    setup_logging()
