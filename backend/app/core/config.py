#app/core/config.py
"""
Application-wide configuration.

Loads settings from environment variables / .env file using pydantic-settings.
Import `settings` anywhere it's needed:

    from app.core.config import settings
"""
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    PROJECT_NAME: str = "Ecommerce Engine"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "example_neon_db_url"

    # --- JWT / Security ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS ---
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

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
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance so .env is only parsed once. No extra calls to the filesystem are made after the first call."""
    return Settings()


settings = get_settings()
