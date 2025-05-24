"""tool to start a debug pod in a Kubernetes deployment"""

import json
import os
import random
import string
from typing import Annotated, List, Optional

import typer

from .console import console
from .func import (
    get_deployment_info, get_kubectl, get_kube_version, create_network_policy, 
    delete_network_policy, get_user_identifier, list_debug_sessions, 
    get_debug_session, terminate_debug_session, resume_debug_session
)


def main(
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
    console.print(
        f"Starting [bold magenta]{deployment}[/bold magenta] "
        f"in [bold magenta]{namespace}[/bold magenta]!"
        " [bold red]>[/]"
    )
    console.print(
        ":hotsprings: Please relax for a moment. We're checking your environment."
    )

    # Check the current cluster version.
    kube_version = get_kube_version(context)
    if not kube_version:
        raise typer.Exit(code=1)

    console.print(
        ":anchor: Your detected [bold purple]cluster version[/bold purple] is",
        kube_version,
        "so we've going to adjust the universe to suit this.",
    )

    kubectl = get_kubectl(kube_version)

    # Add overrides
    deployment_info = get_deployment_info(namespace, deployment, context)
    if not deployment_info:
        raise typer.Exit(code=1)

    container_name = deployment_info["spec"]["template"]["spec"]["containers"][0]["name"]
    image = image or deployment_info["spec"]["template"]["spec"]["containers"][0]["image"]
    env = deployment_info["spec"]["template"]["spec"]["containers"][0].get("env", [])
    env_from = deployment_info["spec"]["template"]["spec"]["containers"][0].get("envFrom", None)
    
    # Add custom environment variables
    if env_vars:
        for env_var in env_vars:
            if "=" in env_var:
                key, value = env_var.split("=", 1)
                env.append({"name": key, "value": value})
            else:
                console.print(f":warning: Skipping invalid env var format: {env_var}")
        env = env if env else None
    
    # Build custom resources if specified, otherwise use deployment resources
    resources = deployment_info["spec"]["template"]["spec"]["containers"][0].get("resources", {})
    if any([cpu_request, cpu_limit, memory_request, memory_limit]):
        custom_resources = {}
        if cpu_request or memory_request:
            custom_resources["requests"] = {}
            if cpu_request:
                custom_resources["requests"]["cpu"] = cpu_request
            if memory_request:
                custom_resources["requests"]["memory"] = memory_request
        if cpu_limit or memory_limit:
            custom_resources["limits"] = {}
            if cpu_limit:
                custom_resources["limits"]["cpu"] = cpu_limit
            if memory_limit:
                custom_resources["limits"]["memory"] = memory_limit
        resources = custom_resources
    
    volume_mounts = deployment_info["spec"]["template"]["spec"]["containers"][0].get(
        "volumeMounts", []
    )
    volumes = deployment_info["spec"]["template"]["spec"].get("volumes", [])
    
    # Add PVC mount if specified
    if mount_pvc:
        pvc_volume = {
            "name": "debug-pvc",
            "persistentVolumeClaim": {
                "claimName": mount_pvc
            }
        }
        pvc_mount = {
            "name": "debug-pvc",
            "mountPath": "/mnt/data"
        }
        volumes.append(pvc_volume)
        volume_mounts.append(pvc_mount)
    
    # Convert back to None if empty for clean JSON
    volume_mounts = volume_mounts if volume_mounts else None
    volumes = volumes if volumes else None
    # Build container spec
    container_spec = {
        "name": container_name,
        "image": image,
        "command": [command],
        "args": args if args else [],
        "env": env,
        "envFrom": env_from,
        "resources": resources,
        "stdin": True,
        "stdinOnce": True,
        "tty": not no_tty,
        "volumeMounts": volume_mounts,
    }
    
    # Add working directory if specified
    if working_directory:
        container_spec["workingDir"] = working_directory
    
    # Add security context if specified
    security_context = {}
    if run_as_user is not None:
        security_context["runAsUser"] = run_as_user
    if privileged:
        security_context["privileged"] = True
    if security_context:
        container_spec["securityContext"] = security_context
    
    # Build pod spec
    pod_spec = {
        "spec": {
            "containers": [container_spec],
            "volumes": volumes,
        },
    }
    
    # Add service account if specified
    if service_account:
        pod_spec["spec"]["serviceAccountName"] = service_account
    
    # Add node selector if specified
    if node_selector and "=" in node_selector:
        key, value = node_selector.split("=", 1)
        pod_spec["spec"]["nodeSelector"] = {key: value}
    
    # Add host network if specified
    if host_network:
        pod_spec["spec"]["hostNetwork"] = True
    
    # Add session tracking labels
    labels = {
        "app": "kubectl-application-shell",
        "debug-user": get_user_identifier(),
        "debug-deployment": deployment,
    }
    
    # Add NetworkPolicy targeting label if needed
    if network_policy:
        labels["debug-pod"] = pod_name
    
    pod_spec["metadata"] = {"labels": labels}
    
    kubectl_overrides = json.dumps(pod_spec)

    name_random = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    pod_name = f"debug-{deployment}-{name_random}"

    # Create NetworkPolicy if specified
    policy_name = None
    if network_policy:
        policy_name = create_network_policy(
            namespace=namespace,
            pod_name=pod_name,
            policy_type=network_policy,
            port=network_port,
            port_range=network_port_range,
            context=context
        )
        if not policy_name:
            console.print(":fire: Failed to create NetworkPolicy, continuing without it")

    # Build the base kubectl command
    interactive_flags = "-it" if not no_tty else "-i"
    pod_timeout = timeout or "5m"
    
    cmd_parts = [
        f"{kubectl} run {interactive_flags} --restart=Never --namespace={namespace} ",
        f"--context={context} " if context else " ",
        f"--image={image} --pod-running-timeout={pod_timeout} {pod_name} ",
        f"--overrides='{kubectl_overrides}'",
    ]
    
    base_cmd = "".join(cmd_parts)
    
    # Add session logging if specified
    if session_log:
        # Use script command to log the session
        cmd = f"script -q {session_log} -c \"{base_cmd}\""
        console.print(f":memo: Session will be logged to [bold green]{session_log}[/bold green]")
    else:
        cmd = base_cmd

    if not run:
        # Return the kubectl command for them to run.
        console.print(
            ":rocket: We're ready to go! [bold blue]Run this command to start your shell[/] "
            "(or add `--run` to run it automatically):"
        )
        print(cmd)
        if policy_name:
            console.print(
                f":warning: [bold yellow]Don't forget to clean up the NetworkPolicy:[/bold yellow] "
                f"kubectl delete networkpolicy {policy_name} -n {namespace}"
            )
        console.print(
            f":information: Session will be named [bold green]{pod_name}[/bold green]. "
            f"Use [bold blue]kubeas list-sessions[/bold blue] to see active sessions."
        )
        raise typer.Exit()

    # Run the kubectl command.
    console.print(f":rocket: Running debug session [bold green]{pod_name}[/bold green]!")
    if session_log:
        console.print(f":memo: Logging session to {session_log}")
    
    try:
        exit_code = os.system(cmd)
    finally:
        # Clean up NetworkPolicy if it was created
        if policy_name:
            console.print(":broom: Cleaning up NetworkPolicy...")
            delete_network_policy(namespace, policy_name, context)
        
        # Note about session cleanup
        console.print(f":information: Session [bold yellow]{pod_name}[/bold yellow] is still running. Use [bold blue]kubeas terminate-session {pod_name} -n {namespace}[/bold blue] to clean up.")
