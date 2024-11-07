#!/usr/bin/env python3

import json
import os
import random
import string
import subprocess
import sys
from typing import Optional

import requests
import typer
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from rich import print

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
    with client.ApiClient() as api_client:
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
    deployment_info = subprocess.run(
        [
            "kubectl",
            "get",
            "deployment",
            f"--namespace={namespace}",
            f"{deployment}",
            "-o",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    container = json.loads(deployment_info)["spec"]["template"]["spec"]["containers"][0]
    container_name = container["name"]
    image = image or container["image"]
    env_from = container.get("envFrom", [])
    annotations = json.loads(deployment_info)["metadata"]["annotations"]
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


if __name__ == "__main__":
    typer.run(main)
