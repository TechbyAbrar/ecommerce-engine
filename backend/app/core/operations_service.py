"""Service interfaces for operational CLI commands."""
from datetime import timedelta
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.utils import utc_now
from app.core.config import settings


class OperationsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def healthcheck(self) -> dict[str, str]:
        result: dict[str, str] = {"database": "unavailable", "redis": "not_configured", "celery": "configured", "smtp": "not_configured", "storage": "not_configured", "stripe": "not_configured"}
        try:
            await self.db.execute(text("SELECT 1"))
            result["database"] = "ok"
        except Exception:
            pass
        if settings.SMTP_HOST and settings.SMTP_FROM_EMAIL:
            result["smtp"] = "configured"
        if settings.STRIPE_SECRET_KEY:
            result["stripe"] = "configured"
        return result

    async def cleanup_logs(self) -> int:
        log_dir = Path(settings.LOG_DIR)
        if not log_dir.exists():
            return 0
        cutoff = utc_now() - timedelta(days=settings.LOG_RETENTION_DAYS)
        removed = 0
        for path in log_dir.glob("*.log.*"):
            if path.is_file() and path.stat().st_mtime < cutoff.timestamp():
                path.unlink()
                removed += 1
        return removed

    async def backup_database(self, destination: Path) -> None:
        raise NotImplementedError("Database backup requires a deployment-specific pg_dump integration")

    async def restore_database(self, source: Path) -> None:
        raise NotImplementedError("Database restore requires a deployment-specific pg_restore integration")
