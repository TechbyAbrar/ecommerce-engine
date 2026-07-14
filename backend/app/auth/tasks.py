"""Celery tasks for asynchronous auth-domain work."""
from celery.utils.time import get_exponential_backoff_interval

from app.core.celery import celery_app
from app.core.config import settings
from app.core.email import EmailDeliveryError, EmailService
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=5, acks_late=True)
def send_otp_email(
    self,
    recipient: str,
    code: str,
    purpose: str,
    user_id: str,
    request_id: str | None = None,
) -> None:
    """Send one OTP email and retry transient SMTP failures."""
    context = {"user_id": user_id, "request_id": request_id}
    logger.info("email_send_started", extra=context)
    try:
        EmailService().send_otp(recipient, code, purpose, settings.OTP_EXPIRE_MINUTES)
    except EmailDeliveryError as exc:
        logger.exception(
            "email_send_failed",
            extra={
                **context,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
        )
        if exc.retryable:
            countdown = get_exponential_backoff_interval(
                factor=2,
                retries=self.request.retries,
                maximum=600,
                full_jitter=True,
            )
            raise self.retry(exc=exc, countdown=countdown) from exc
        raise
    except Exception as exc:
        logger.exception(
            "email_send_failed",
            extra={
                **context,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
        )
        raise

    logger.info("email_sent", extra=context)
