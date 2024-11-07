"""support functions for kubectl-application-shell"""

import os
from pathlib import Path

import requests
from kubernetes import client
from kubernetes.client.rest import ApiException
from rich import print


def get_kubectl(version: str) -> Path:
    """get kubectl binary matching the cluster version and host architecture"""

    directory = Path(".kubebin") / version
    if not directory.exists():
        directory.mkdir(parents=True)
        print(
            ":wrench: We're going to download the correct "
            "[bold purple]kubectl[/bold purple] binary for you."
        )

        arch = "amd64" if os.uname().machine == "x86_64" else "arm64"
        kubectl_url = f"https://dl.k8s.io/release/{version}/bin/linux/{arch}/kubectl"
        kubectl_path = directory / "kubectl"
        kubectl_path.write_bytes(
            requests.get(
                kubectl_url,
                allow_redirects=True,
                timeout=5,
            ).content
        )
        kubectl_path.chmod(0o755)

    print(":sun: Kubectl resolved!")

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
