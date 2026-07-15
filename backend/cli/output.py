from rich.console import Console

console = Console()


def success(message: str) -> None:
    console.print(f"[green]✓[/green] {message}")


def error(message: str) -> None:
    console.print(f"[red]Error:[/red] {message}")
