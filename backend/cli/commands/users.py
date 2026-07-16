import typer

from app.auth.schemas import UserCreate
from app.auth.service import AuthService
from app.common.enums import UserRole
from cli.dependencies import session_scope
from cli.prompts import required


async def create_account(email: str | None, password: str | None, full_name: str | None, role: UserRole, force: bool = False) -> str:
    async for db in session_scope():
        user = await AuthService(db).create_administrative_user(
            UserCreate(email=required(email, "Email"), password=required(password, "Password", hide_input=True), full_name=full_name),
            role,
            force=force,
        )
        return user.email


async def change_role(email: str, role: UserRole, *, promote: bool) -> str:
    async for db in session_scope():
        service = AuthService(db)
        user = await (service.promote_user(email, role) if promote else service.demote_user(email, role))
        return user.email


async def reset_password(email: str | None, password: str | None) -> str:
    email = required(email, "Email")
    async for db in session_scope():
        await AuthService(db).admin_reset_password(email, required(password, "New password", hide_input=True))
        return email
