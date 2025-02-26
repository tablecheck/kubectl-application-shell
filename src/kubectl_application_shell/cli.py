"""CLI entry point for the kubectl_application_shell package."""

import typer

from .app import main

app = typer.Typer(add_completion=False)
app.command()(main)


if __name__ == "__main__":
    app()
