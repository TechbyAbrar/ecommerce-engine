import asyncio
import typer
from cli.commands.users import create_account
from cli.output import success


def register(app: typer.Typer) -> None:
    @app.command()
    def createsuperuser(email: str | None = None, password: str | None = typer.Option(None, prompt=False, hide_input=True), full_name: str | None = None, force: bool = False) -> None:
        from app.common.enums import UserRole
        success(f"Superuser {asyncio.run(create_account(email, password, full_name, UserRole.SUPERUSER, force))} created")
