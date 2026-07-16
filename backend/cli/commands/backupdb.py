"""Database backup command; implementation is deployment-owned."""
from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from app.core.operations_service import OperationsService
from cli.dependencies import session_scope
from cli.output import success


def register(app: typer.Typer) -> None:
    @app.command()
    def backupdb(destination: Path = typer.Argument(..., help="Destination backup file.")) -> None:
        """Back up PostgreSQL using the configured operations service."""

        async def run() -> None:
            async for db in session_scope():
                await OperationsService(db).backup_database(destination)

        asyncio.run(run())
        success(f"Database backup created at {destination}")
