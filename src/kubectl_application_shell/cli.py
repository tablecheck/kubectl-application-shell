"""CLI entry point for the kubectl_application_shell package."""

import os
from typing import Annotated, Optional, List

import typer
from rich.table import Table

from .console import console
from .func import (
    get_kubectl, get_kube_version, list_debug_sessions, 
    terminate_debug_session, resume_debug_session
)

app = typer.Typer(add_completion=False)


# Main command for creating debug sessions
@app.command(name="main", help="produce a debug pod for a Kubernetes deployment")
def main_command(
    namespace: Annotated[
        str,
        typer.Argument(help="The namespace of the deployment."),
    ],
    deployment: Annotated[
        str,
        typer.Argument(help="The deployment to debug."),
    ],
    context: Annotated[
        Optional[str],
        typer.Option(help="The kubeconfig context to use.", show_default=False),
    ] = None,
    image: Annotated[
        Optional[str],
        typer.Option(help="The image to run in the debug pod.", show_default=False),
    ] = None,
    command: Annotated[
        str,
        typer.Argument(help="The command/entrypoint/shell to run in the debug pod."),
    ] = "/bin/bash",
    args: Annotated[
        List[str],
        typer.Argument(help="The arguments to pass to the command/entrypoint/shell."),
    ] = None,
    cpu_request: Annotated[
        Optional[str],
        typer.Option("--cpu-request", help="CPU request for the debug pod (e.g., '100m', '0.5').", show_default=False),
    ] = None,
    cpu_limit: Annotated[
        Optional[str],
        typer.Option("--cpu-limit", help="CPU limit for the debug pod (e.g., '500m', '1').", show_default=False),
    ] = None,
    memory_request: Annotated[
        Optional[str],
        typer.Option("--memory-request", help="Memory request for the debug pod (e.g., '256Mi', '1Gi').", show_default=False),
    ] = None,
    memory_limit: Annotated[
        Optional[str],
        typer.Option("--memory-limit", help="Memory limit for the debug pod (e.g., '512Mi', '2Gi').", show_default=False),
    ] = None,
    network_policy: Annotated[
        Optional[str],
        typer.Option("--network-policy", help="NetworkPolicy type: block-all-ingress, block-all-egress, block-all, allow-port, allow-port-range", show_default=False),
    ] = None,
    network_port: Annotated[
        Optional[str],
        typer.Option("--network-port", help="Port number to allow (used with allow-port policy)", show_default=False),
    ] = None,
    network_port_range: Annotated[
        Optional[str],
        typer.Option("--network-port-range", help="Port range to allow, e.g. '8000-8080' (used with allow-port-range policy)", show_default=False),
    ] = None,
    session_log: Annotated[
        Optional[str],
        typer.Option("--session-log", help="File path to log the session output.", show_default=False),
    ] = None,
    service_account: Annotated[
        Optional[str],
        typer.Option("--service-account", help="Service account to use for RBAC permissions.", show_default=False),
    ] = None,
    env_vars: Annotated[
        Optional[List[str]],
        typer.Option("--env", help="Environment variables to set (format: KEY=VALUE). Can be used multiple times.", show_default=False),
    ] = None,
    working_directory: Annotated[
        Optional[str],
        typer.Option("--workdir", help="Working directory for the debug pod.", show_default=False),
    ] = None,
    node_selector: Annotated[
        Optional[str],
        typer.Option("--node-selector", help="Node selector constraint (format: KEY=VALUE).", show_default=False),
    ] = None,
    timeout: Annotated[
        Optional[str],
        typer.Option("--timeout", help="Pod running timeout (default: 5m).", show_default=False),
    ] = None,
    mount_pvc: Annotated[
        Optional[str],
        typer.Option("--mount-pvc", help="PVC to mount at /mnt/data.", show_default=False),
    ] = None,
    no_tty: Annotated[
        bool,
        typer.Option("--no-tty", help="Disable TTY allocation (non-interactive mode)."),
    ] = False,
    privileged: Annotated[
        bool,
        typer.Option("--privileged", help="Run in privileged mode for system debugging."),
    ] = False,
    host_network: Annotated[
        bool,
        typer.Option("--host-network", help="Use host network for network debugging."),
    ] = False,
    run_as_user: Annotated[
        Optional[int],
        typer.Option("--run-as-user", help="User ID to run as.", show_default=False),
    ] = None,
    run: Annotated[
        bool,
        typer.Option("--run", help="Run the debug pod."),
    ] = False,
) -> None:
    """produce a debug pod for a Kubernetes deployment"""
    from .app import main
    # Call the actual main function with all parameters
    main(
        namespace=namespace,
        deployment=deployment,
        context=context,
        image=image,
        command=command,
        args=args,
        cpu_request=cpu_request,
        cpu_limit=cpu_limit,
        memory_request=memory_request,
        memory_limit=memory_limit,
        network_policy=network_policy,
        network_port=network_port,
        network_port_range=network_port_range,
        session_log=session_log,
        service_account=service_account,
        env_vars=env_vars,
        working_directory=working_directory,
        node_selector=node_selector,
        timeout=timeout,
        mount_pvc=mount_pvc,
        no_tty=no_tty,
        privileged=privileged,
        host_network=host_network,
        run_as_user=run_as_user,
        run=run
    )


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
