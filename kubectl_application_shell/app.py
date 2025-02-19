"""tool to start a debug pod in a Kubernetes deployment"""

import json
import os
import random
import string
from typing import Annotated, List, Optional

import typer
import typer.cli

from .console import console
from .func import get_deployment_info, get_kubectl, get_kube_version


def main(
    namespace: Annotated[
        str,
        typer.Argument(help="The namespace of the deployment."),
    ],
    deployment: Annotated[
        str,
        typer.Argument(help="The deployment to debug."),
    ],
    image: Annotated[
        Optional[str],
        typer.Option(help="The image to run in the debug pod.", show_default=False),
    ] = None,
    shell: Annotated[
        str,
        typer.Option(help="The shell to run in the debug pod."),
    ] = "/bin/bash",
    args: Annotated[
        List[str],
        typer.Option(help="The arguments to pass to the shell."),
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
    kube_version = get_kube_version()
    if not kube_version:
        raise typer.Exit(code=1)

    console.print(
        ":anchor: Your detected [bold purple]cluster version[/bold purple] is",
        kube_version,
        "so we've going to adjust the universe to suit this.",
    )

    kubectl = get_kubectl(kube_version)

    # Add overrides
    deployment_info = get_deployment_info(namespace, deployment)
    if not deployment_info:
        raise typer.Exit(code=1)

    container_name = deployment_info["spec"]["template"]["spec"]["containers"][0]["name"]
    image = image or deployment_info["spec"]["template"]["spec"]["containers"][0]["image"]
    env = deployment_info["spec"]["template"]["spec"]["containers"][0].get("env", None)
    env_from = deployment_info["spec"]["template"]["spec"]["containers"][0].get("envFrom", None)
    resources = deployment_info["spec"]["template"]["spec"]["containers"][0].get("resources", None)
    volume_mounts = deployment_info["spec"]["template"]["spec"]["containers"][0].get(
        "volumeMounts", None
    )
    volumes = deployment_info["spec"]["template"]["spec"].get("volumes", None)
    kubectl_overrides = json.dumps(
        {
            "spec": {
                "containers": [
                    {
                        "name": container_name,
                        "image": image,
                        "command": [shell],
                        "args": args if args else [],
                        "env": env,
                        "envFrom": env_from,
                        "resources": resources,
                        "stdin": True,
                        "stdinOnce": True,
                        "tty": True,
                        "volumeMounts": volume_mounts,
                    }
                ],
                "volumes": volumes,
            },
        }
    )

    name_random = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))

    cmd = "".join(
        [
            f"{kubectl} run -it --rm --restart=Never --namespace={namespace} ",
            f"--image={image} --pod-running-timeout=5m debug-{deployment}-{name_random} ",
            f"--overrides='{kubectl_overrides}' -- {shell}",
        ]
    )

    if not run:
        # Return the kubectl command for them to run.
        console.print(
            ":rocket: We're ready to go! [bold blue]Run this command to start your shell[/] "
            "(or add `--run` to run it automatically):"
        )
        print(cmd)
        raise typer.Exit()

    # Run the kubectl command.
    console.print(":rocket: Running the debug pod!")
    os.system(cmd)
