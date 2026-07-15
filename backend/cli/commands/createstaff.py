import asyncio
import typer
from cli.commands.users import create_account
from cli.output import success

def register(app: typer.Typer) -> None:
    @app.command()
    def createstaff(email: str | None = None, password: str | None = typer.Option(None, prompt=False, hide_input=True), full_name: str | None = None) -> None:
        from app.common.enums import UserRole
        success(f"Staff account {asyncio.run(create_account(email, password, full_name, UserRole.STAFF))} created")
