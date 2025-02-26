"""support functions for kubectl-application-shell"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import requests
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from rich.progress import Progress, SpinnerColumn, TextColumn
from urllib3.exceptions import MaxRetryError

from .console import console

def get_api_client(context: str = None) -> client.ApiClient:
    """get a kubernetes API client"""

    try:
        config.load_kube_config(context=context)
    except config.config_exception.ConfigException:
        config.load_incluster_config()

    return client.ApiClient()


def get_kube_version(context: str = None) -> Optional[str]:
    """get the version of the kubernetes cluster"""

    api_client = get_api_client(context)

    try:
        version = client.VersionApi(api_client).get_code()
    except (ApiException, MaxRetryError) as e:
        console.print(":fire: Unable to get cluster version:", e.reason)
        return None

    return version.git_version.split("+")[0].split("-")[0]


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
    namespace: str,
    deployment: str,
    context: str = None,
) -> Optional[dict]:
    """get deployment info"""

    apps_v1 = client.AppsV1Api(get_api_client(context))
    try:
        deployment_info = apps_v1.read_namespaced_deployment(
            name=deployment, namespace=namespace, _preload_content=False
        )
    except (ApiException, MaxRetryError) as e:
        console.print(":fire: Unable to get deployment info:", e.reason)
        return None

    return json.loads(deployment_info.data)
