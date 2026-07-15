"""Infrastructure health-check command."""
from __future__ import annotations

import asyncio

import typer

from app.core.operations_service import OperationsService
from cli.dependencies import session_scope
from cli.output import success


def register(app: typer.Typer) -> None:
    @app.command()
    def healthcheck() -> None:
        """Report configured infrastructure and database availability."""

        async def run() -> dict[str, str]:
            async for db in session_scope():
                return await OperationsService(db).healthcheck()
            return {}

        results = asyncio.run(run())
        for name, status in results.items():
            typer.echo(f"{name}: {status}")
        if results.get("database") != "ok":
            raise typer.Exit(code=1)
        success("Health check completed")
