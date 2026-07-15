"""Database restore command; implementation is deployment-owned."""
from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from app.core.operations_service import OperationsService
from cli.dependencies import session_scope
from cli.output import success


def register(app: typer.Typer) -> None:
    @app.command()
    def restoredb(source: Path = typer.Argument(..., exists=True, readable=True, help="Backup file to restore.")) -> None:
        """Restore PostgreSQL using the configured operations service."""

        async def run() -> None:
            async for db in session_scope():
                await OperationsService(db).restore_database(source)

        asyncio.run(run())
        success(f"Database restored from {source}")
