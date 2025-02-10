"""tool to start a debug pod in a Kubernetes deployment"""

import json
import os
import random
import string
from typing import Annotated, Optional

import typer
import typer.cli
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from urllib3.exceptions import HTTPError

from .console import console
from .func import get_deployment_info, get_kubectl

config.load_kube_config()


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
    api_client = client.ApiClient()

    try:
        api_response = client.VersionApi(api_client).get_code()
        kube_version = api_response.git_version.split("-")[0].rpartition("+")[0]
        console.print(
            ":anchor: Your detected [bold purple]cluster version[/bold purple] is",
            kube_version,
            "so we've going to adjust the universe to suit this.",
        )

    except (ApiException, HTTPError) as e:
        print(f"Exception when calling VersionApi->get_code: %{e}\n")
        raise typer.Exit(code=1)

    kubectl = get_kubectl(kube_version)

    # Add overrides
    try:
        deployment_info = get_deployment_info(api_client, namespace, deployment)
    except ApiException as e:
        print(f"Exception when calling AppsV1Api->read_namespaced_deployment: %{e}\n")
        raise typer.Exit(code=1)

    container_name = deployment_info.spec.template.spec.containers[0].name
    image = image or deployment_info.spec.template.spec.containers[0].image
    env_from = deployment_info.spec.template.spec.containers[0].env_from
    kubectl_overrides = json.dumps(
        {
            "spec": {
                "containers": [
                    {
                        "name": container_name,
                        "image": image,
                        "command": [shell],
                        "envFrom": env_from,
                        "stdin": True,
                        "stdinOnce": True,
                        "tty": True,
                    }
                ]
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
