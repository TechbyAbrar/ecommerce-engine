"""Expired log cleanup command."""
from __future__ import annotations

import asyncio

import typer

from app.core.operations_service import OperationsService
from cli.dependencies import session_scope
from cli.output import success


def register(app: typer.Typer) -> None:
    @app.command()
    def cleanuplogs() -> None:
        """Remove rotated logs older than the configured retention period."""

        async def run() -> int:
            async for db in session_scope():
                return await OperationsService(db).cleanup_logs()
            return 0

        removed = asyncio.run(run())
        success(f"Removed {removed} expired log file(s)")
