"""Minimal SMTP email sender. It intentionally never logs message bodies or OTPs."""
import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import settings


class EmailDeliveryError(Exception):
    """Raised when SMTP is unavailable or rejects a message."""


class EmailService:
    async def send_otp(self, recipient: str, code: str, purpose: str, expires_in_minutes: int) -> None:
        subject = "Verify your email" if purpose == "email_verification" else "Your security code"
        message = (
            f"Your {settings.PROJECT_NAME} security code is: {code}\n\n"
            f"It expires in {expires_in_minutes} minutes. Do not share this code with anyone."
        )
        await asyncio.to_thread(self._send, recipient, subject, message)

    def _send(self, recipient: str, subject: str, body: str) -> None:
        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            raise EmailDeliveryError("SMTP is not configured")

        email = EmailMessage()
        email["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        email["To"] = recipient
        email["Subject"] = subject
        email.set_content(body)

        try:
            smtp_class = smtplib.SMTP_SSL if settings.SMTP_USE_SSL else smtplib.SMTP
            with smtp_class(
                settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT_SECONDS
            ) as smtp:
                if settings.SMTP_USE_STARTTLS and not settings.SMTP_USE_SSL:
                    smtp.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD.get_secret_value())
                smtp.send_message(email)
        except (OSError, smtplib.SMTPException) as exc:
            raise EmailDeliveryError("Unable to send email") from exc
