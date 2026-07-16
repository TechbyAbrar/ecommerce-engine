#app/core/config.py
"""
Application-wide configuration.

Loads settings from environment variables / .env file using pydantic-settings.
Import `settings` anywhere it's needed:

    from app.core.config import settings
"""
from functools import lru_cache

from pydantic import EmailStr, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    PROJECT_NAME: str = "Ecommerce Engine"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "example_neon_db_url"

    # --- Celery / Redis ---
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # --- JWT / Security ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCK_MINUTES: int = 15

    # --- Email / OTP ---
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: SecretStr | None = None
    SMTP_USE_SSL: bool = False
    SMTP_USE_STARTTLS: bool = True
    SMTP_FROM_EMAIL: EmailStr | None = None
    SMTP_FROM_NAME: str = "Ecommerce Engine"
    SMTP_TIMEOUT_SECONDS: int = 10
    OTP_LENGTH: int = 6
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_COOLDOWN_SECONDS: int = 60

    # --- Logging ---
    LOG_LEVEL: str | None = None
    LOG_DIR: str = "logs"
    LOG_RETENTION_DAYS: int = 7

    # --- CORS ---
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # --- Payments ---
    STRIPE_SECRET_KEY: SecretStr | None = None
    STRIPE_CURRENCY: str = "usd"
    STRIPE_WEBHOOK_SECRET: SecretStr | None = None

    # --- Product uploads ---
    PRODUCT_IMAGE_STORAGE_PATH: str = "media/products/originals"
    PRODUCT_IMAGE_ALLOWED_CONTENT_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}
    PRODUCT_IMAGE_MAX_SIZE_BYTES: int = 5 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.ENVIRONMENT.lower() == "production" and (
            self.SECRET_KEY == "CHANGE_ME_IN_PRODUCTION" or len(self.SECRET_KEY) < 32
        ):
            raise ValueError("SECRET_KEY must be a unique value of at least 32 characters in production")
        if self.SMTP_USE_SSL and self.SMTP_USE_STARTTLS:
            raise ValueError("SMTP_USE_SSL and SMTP_USE_STARTTLS cannot both be enabled")
        if self.OTP_LENGTH < 6 or self.OTP_MAX_ATTEMPTS < 1 or self.OTP_EXPIRE_MINUTES < 1:
            raise ValueError("OTP security settings are invalid")
        if self.MAX_LOGIN_ATTEMPTS < 1 or self.ACCOUNT_LOCK_MINUTES < 1:
            raise ValueError("Account lock settings are invalid")
        if self.LOG_RETENTION_DAYS < 1:
            raise ValueError("LOG_RETENTION_DAYS must be at least 1")
        if self.PRODUCT_IMAGE_MAX_SIZE_BYTES < 1:
            raise ValueError("PRODUCT_IMAGE_MAX_SIZE_BYTES must be at least 1")
        if not self.PRODUCT_IMAGE_ALLOWED_CONTENT_TYPES:
            raise ValueError("PRODUCT_IMAGE_ALLOWED_CONTENT_TYPES must not be empty")
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance so .env is only parsed once. No extra calls to the filesystem are made after the first call."""
    return Settings()


settings = get_settings()
