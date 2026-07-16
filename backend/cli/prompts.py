import typer


def required(value: str | None, label: str, *, hide_input: bool = False) -> str:
    return value if value is not None else typer.prompt(label, hide_input=hide_input)
