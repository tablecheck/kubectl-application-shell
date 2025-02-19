"""support functions for kubectl-application-shell"""

import os
import sys
from pathlib import Path

import requests
from kubernetes import client
from kubernetes.client.rest import ApiException
from rich.progress import Progress, SpinnerColumn, TextColumn

from .console import console


def get_kubectl(version: str) -> Path:
    """get kubectl binary matching the cluster version and host architecture"""

    directory = Path.home() / Path(".cache/kubectl-application-shell") / version
    if not directory.exists():
        directory.mkdir(parents=True)
        console.print(
            ":wrench: We're going to download the correct "
            "[bold purple]kubectl[/bold purple] binary for you."
        )

        arch = "amd64" if os.uname().machine == "x86_64" else "arm64"
        kubectl_url = f"https://dl.k8s.io/release/{version}/bin/{sys.platform}/{arch}/kubectl"
        kubectl_path = directory / "kubectl"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(
                ":wheel_of_dharma: Downloading kubectl...", total=None
            )
            kubectl_path.write_bytes(
                requests.get(
                    kubectl_url,
                    allow_redirects=True,
                    timeout=5,
                    hooks={
                        "response": lambda r, *args, **kwargs: progress.update(
                            task,
                            advance=len(r.content),
                        ),
                    },
                ).content
            )
            kubectl_path.chmod(0o755)

    console.print(":sun: Kubectl resolved!")

    return directory / "kubectl"


def get_deployment_info(
    api_client: client.ApiClient,
    namespace: str,
    deployment: str,
):
    """get deployment info"""

    apps_v1 = client.AppsV1Api(api_client)
    try:
        deployment_info = apps_v1.read_namespaced_deployment(
            name=deployment, namespace=namespace
        )
        return deployment_info
    except ApiException as e:
        return e
