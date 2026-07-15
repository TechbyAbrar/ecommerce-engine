import asyncio
import typer
from app.core.reference_service import ReferenceDataService
from cli.dependencies import session_scope
from cli.output import success

def register(app: typer.Typer) -> None:
    @app.command()
    def seed() -> None:
        async def run() -> int:
            async for db in session_scope(): return await ReferenceDataService(db).seed()
        success(f"Seeded {asyncio.run(run())} reference-data records")
