#!/usr/bin/env python3

import json
import os
import random
import string
import sys
from typing import Optional

import requests
import typer
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from rich import print

from .func import get_deployment_info

config.load_kube_config()


def main(
    namespace: str,
    deployment: str,
    # size: Optional[str] = typer.Argument(None),
    image: Optional[str] = typer.Option(None),
):
    print(
        f"Starting [bold magenta]{deployment}[/bold magenta] "
        f"in [bold magenta]{namespace}[/bold magenta]!"
        " [bold red]>[/]"
    )
    print(":hotsprings: Please relax for a moment. We're checking your environment.")

    # Check the current cluster version.
    api_client = client.ApiClient()
    api_instance = client.VersionApi(api_client)

    try:
        api_response = api_instance.get_code()
        kube_version = api_response.git_version.split("-")[0].rpartition("+")[0]
        print(
            ":anchor: Your detected [bold purple]cluster version[/bold purple] is",
            kube_version,
            "so we've going to adjust the universe to suit this.",
        )

    except ApiException as e:
        print(f"Exception when calling VersionApi->get_code: %{e}\n")
        sys.exit(1)

    # Check if the correct Kubernetes binary exists on this machine.
    directory = os.path.dirname(".kubebin/" + kube_version + "/kubectl")
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(
            ":wrench: We're going to download the correct "
            "[bold purple]kubectl[/bold purple] binary for you."
        )

        response = requests.get(
            f"https://dl.k8s.io/release/{kube_version}/bin/darwin/arm64/kubectl",
            allow_redirects=True,
            timeout=5,
        )
        open(f"{directory}/kubectl", "wb").write(response.content)
        os.chmod(f"{directory}/kubectl", 0o755)

    print(":sun: Kubectl resolved!")

    # Add overrides
    try:
        deployment_info = get_deployment_info(api_client, namespace, deployment)
    except ApiException as e:
        print(f"Exception when calling AppsV1Api->read_namespaced_deployment: %{e}\n")
        sys.exit(1)

    container_name = deployment_info.spec.template.spec.containers[0].name
    image = image or deployment_info.spec.template.spec.containers[0].image
    env_from = deployment_info.spec.template.spec.containers[0].env_from
    annotations = deployment_info.metadata.annotations
    del annotations["kubectl.kubernetes.io/last-applied-configuration"]
    kubectl_overrides = json.dumps(
        {
            "metadata": {
                "annotations": annotations,
            },
            "spec": {
                "containers": [
                    {
                        "name": container_name,
                        "image": image,
                        "args": ["/bin/bash"],
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

    # Return the kubectl command for them to run.
    print(
        ":rocket: We're ready to go! [bold blue]Run this command to start your shell[/bold blue]:"
    )
    sys.exit(
        f".kubebin/{kube_version}/kubectl run -it --rm --restart=Never --namespace={namespace} "
        f"--image={image} --pod-running-timeout=5m debug-{deployment}-{name_random} "
        f"--overrides='{kubectl_overrides}' -- /bin/bash"
    )
