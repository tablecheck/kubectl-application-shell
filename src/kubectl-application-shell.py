#!/usr/bin/env python3

# CLI imports
from rich import print
import typer
import json
from typing import Optional
import requests
import subprocess
import os
import sys
import random
import string

# Kubernetes imports
from kubernetes import client, config
from kubernetes.client.rest import ApiException

config.load_kube_config()

def main(namespace: str, deployment: str, size: Optional[str] = typer.Argument(None)):
    print(f"Starting [bold magenta]{deployment}[/bold magenta] in [bold magenta]{namespace}[/bold magenta]!", " [bold red]>[/]")
    print(":hotsprings: Please relax for a moment. We're checking your environment.")

    # Check the current cluster version.
    with client.ApiClient() as api_client:
        api_instance = client.VersionApi(api_client)

        try:
            api_response = api_instance.get_code()
            kube_version = api_response.git_version.split('-')[0]
            print(
                ":anchor: Your detected [bold purple]cluster version[/bold purple] is",
                kube_version,
                "so we've going to adjust the universe to suit this."
            )


        except ApiException as e:
            print("Exception when calling VersionApi->get_code: %s\n" % e)

    # Check if the correct Kubernetes binary exists on this machine.
    directory = os.path.dirname(".kubebin/" + kube_version + "/kubectl")
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(":wrench: We're going to download the correct [bold purple]kubectl[/bold purple] binary for you.")

        response = requests.get(f'https://dl.k8s.io/release/{kube_version}/bin/darwin/arm64/kubectl',
                                allow_redirects=True)
        open(f'{directory}/kubectl', 'wb').write(response.content)
        os.chmod(f'{directory}/kubectl', 0o755)

    print(f":sun: We're ready to go!")

    # Add overrides
    deployment_info = subprocess.run(['kubectl', 'get', 'deployment', f"--namespace={namespace}", f"{deployment}", "-o", 'json'], capture_output=True, text=True).stdout
    container_name = json.loads(deployment_info)['spec']['template']['spec']['containers'][0]['name']
    image = json.loads(deployment_info)['spec']['template']['spec']['containers'][0]['image']
    env_from = json.loads(deployment_info)['spec']['template']['spec']['containers'][0]['envFrom']
    annotations = json.loads(deployment_info)['spec']['template']['metadata']['annotations']
    kubectl_overrides = json.dumps({
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
      }
    }).replace('"', '\\"')
    print(kubectl_overrides)

    name_random = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

    # Return the kubectl command for them to run.
    print(f":rocket: We're ready to go! [bold blue]Run this command to start your shell[/bold blue]:")
    sys.exit(f'.kubebin/{kube_version}/kubectl run -it --rm --restart=Never --namespace={namespace} --image={image} --pod-running-timeout=5m debug-{deployment}-{name_random} --overrides="$(echo \"{kubectl_overrides}\" | jq -c .)" -- /bin/bash')


if __name__ == "__main__":
    typer.run(main)

