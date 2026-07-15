import asyncio
import typer
from app.common.enums import UserRole
from cli.commands.users import change_role
from cli.output import success

def register(app: typer.Typer) -> None:
    @app.command()
    def demoteuser(email: str, role: UserRole = UserRole.USER) -> None:
        success(f"Demoted {asyncio.run(change_role(email, role, promote=False))}")
