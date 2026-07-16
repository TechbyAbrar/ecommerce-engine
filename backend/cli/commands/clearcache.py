import asyncio
import typer
from app.products.service import ProductService
from cli.dependencies import session_scope
from cli.output import success

def register(app: typer.Typer) -> None:
    @app.command()
    def clearcache() -> None:
        async def run() -> bool:
            async for db in session_scope(): return await ProductService(db).clear_cache()
        if not asyncio.run(run()): raise typer.Exit(1)
        success("Product cache cleared")
