import asyncio
import typer
from cli.commands.users import reset_password
from cli.output import success

def register(app: typer.Typer) -> None:
    @app.command()
    def resetpassword(email: str | None = None, password: str | None = typer.Option(None, prompt=False, hide_input=True)) -> None:
        success(f"Password reset for {asyncio.run(reset_password(email, password))}")
