"""Typer entry point for administrative management commands.

Run commands with ``python -m cli.manage <command>`` from the backend
directory. Command modules only collect terminal input and delegate work to
the application service layer.
"""
from __future__ import annotations

import typer

from app.core.exceptions import AppException
from cli.commands import (
    backupdb,
    clearcache,
    cleanuplogs,
    createsuperuser,
    createstaff,
    createuser,
    demoteuser,
    healthcheck,
    promoteuser,
    resetpassword,
    restoredb,
    seed,
)
from cli.output import error

app = typer.Typer(
    name="manage",
    help="Administrative management commands for Ecommerce Engine.",
    no_args_is_help=True,
)

for command_module in (
    createsuperuser,
    createstaff,
    createuser,
    promoteuser,
    demoteuser,
    resetpassword,
    seed,
    clearcache,
    backupdb,
    restoredb,
    healthcheck,
    cleanuplogs,
):
    command_module.register(app)


def main() -> None:
    """Run the CLI and render handled application errors consistently."""
    try:
        app()
    except AppException as exc:
        error(exc.message)
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        error(str(exc))
        raise typer.Exit(code=1) from exc
    except NotImplementedError as exc:
        error(str(exc))
        raise typer.Exit(code=2) from exc


if __name__ == "__main__":
    main()
