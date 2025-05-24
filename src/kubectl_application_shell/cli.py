"""CLI entry point for the kubectl_application_shell package."""

import os
from typing import Annotated, Optional

import typer
from rich.table import Table

from .app import main
from .console import console
from .func import (
    get_kubectl, get_kube_version, list_debug_sessions, 
    terminate_debug_session, resume_debug_session
)

app = typer.Typer(add_completion=False)

# Main command for creating debug sessions
app.command()(main)


@app.command("list-sessions")
def list_sessions(
    namespace: Annotated[
        Optional[str],
        typer.Option("-n", "--namespace", help="Namespace to list sessions from (all namespaces if not specified)"),
    ] = None,
    context: Annotated[
        Optional[str],
        typer.Option(help="The kubeconfig context to use.", show_default=False),
    ] = None,
) -> None:
    """List active debug sessions"""
    
    sessions = list_debug_sessions(namespace, context)
    
    if not sessions:
        if namespace:
            console.print(f":information: No active debug sessions found in namespace [bold]{namespace}[/bold]")
        else:
            console.print(":information: No active debug sessions found")
        return
    
    # Create table for display
    table = Table(title="Active Debug Sessions")
    table.add_column("Session Name", style="cyan")
    table.add_column("Namespace", style="magenta")
    table.add_column("User", style="green")
    table.add_column("Deployment", style="blue")
    table.add_column("Status", style="yellow")
    table.add_column("Created", style="dim")
    table.add_column("Node", style="dim")
    
    for session in sessions:
        table.add_row(
            session["name"],
            session["namespace"],
            session["user"],
            session["deployment"],
            session["status"],
            session["created"],
            session["node"]
        )
    
    console.print(table)


@app.command("resume-session")
def resume_session_cmd(
    session_name: Annotated[str, typer.Argument(help="Name of the debug session to resume")],
    namespace: Annotated[
        str,
        typer.Option("-n", "--namespace", help="Namespace of the session"),
    ],
    context: Annotated[
        Optional[str],
        typer.Option(help="The kubeconfig context to use.", show_default=False),
    ] = None,
    session_log: Annotated[
        Optional[str],
        typer.Option("--session-log", help="File path to log the session output.", show_default=False),
    ] = None,
    no_tty: Annotated[
        bool,
        typer.Option("--no-tty", help="Disable TTY allocation (non-interactive mode)."),
    ] = False,
    run: Annotated[
        bool,
        typer.Option("--run", help="Execute immediately instead of showing the command."),
    ] = False,
) -> None:
    """Resume an existing debug session"""
    
    # Get kubectl binary
    kube_version = get_kube_version(context)
    if not kube_version:
        raise typer.Exit(code=1)
    
    kubectl = get_kubectl(kube_version)
    
    # Generate resume command
    cmd = resume_debug_session(
        session_name=session_name,
        namespace=namespace,
        kubectl_path=kubectl,
        context=context,
        session_log=session_log,
        no_tty=no_tty
    )
    
    if not cmd:
        raise typer.Exit(code=1)
    
    if not run:
        console.print(
            f":arrows_counterclockwise: Ready to resume session [bold green]{session_name}[/bold green]! "
            "[bold blue]Run this command:[/bold blue]"
        )
        print(cmd)
        return
    
    # Execute the resume command
    console.print(f":arrows_counterclockwise: Resuming session [bold green]{session_name}[/bold green]...")
    if session_log:
        console.print(f":memo: Logging session to {session_log}")
    
    os.system(cmd)


@app.command("terminate-session")
def terminate_session_cmd(
    session_name: Annotated[str, typer.Argument(help="Name of the debug session to terminate")],
    namespace: Annotated[
        str,
        typer.Option("-n", "--namespace", help="Namespace of the session"),
    ],
    context: Annotated[
        Optional[str],
        typer.Option(help="The kubeconfig context to use.", show_default=False),
    ] = None,
) -> None:
    """Terminate a debug session"""
    
    success = terminate_debug_session(session_name, namespace, context)
    if not success:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
