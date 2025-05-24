"""support functions for kubectl-application-shell"""

import json
import os
import sys
from pathlib import Path
from shutil import which
from typing import Optional, List, Dict
import getpass

import requests
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
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
        kubectl_url = (
            f"https://dl.k8s.io/release/{version}/bin/{sys.platform}/{arch}/kubectl"
        )
        kubectl_path = directory / "kubectl"

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            SpinnerColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task(
                ":wheel_of_dharma: Downloading kubectl...", total=None
            )
            try:
                response = requests.get(
                    kubectl_url,
                    allow_redirects=True,
                    timeout=5,
                    stream=True,
                )
                progress.update(
                    task,
                    total=int(response.headers.get("Content-Length", 0)),
                )
                for data in response.iter_content(chunk_size=32768):
                    with kubectl_path.open("ab") as f:
                        f.write(data)
                    progress.update(task, advance=len(data))
                kubectl_path.chmod(0o755)
            except requests.exceptions.RequestException as e:
                console.print(":fire: Unable to download kubectl:", e)
                console.print(":fire: Falling back to kubectl in $PATH.")
                directory.rmdir()
                return which("kubectl")

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


def create_network_policy(
    namespace: str,
    pod_name: str,
    policy_type: str,
    port: str = None,
    port_range: str = None,
    context: str = None,
) -> Optional[str]:
    """create a NetworkPolicy for the debug pod"""
    
    network_v1 = client.NetworkingV1Api(get_api_client(context))
    
    # Base policy name
    policy_name = f"debug-{pod_name}-netpol"
    
    # Base pod selector
    pod_selector = client.V1LabelSelector(
        match_labels={"debug-pod": pod_name}
    )
    
    # Define policy templates
    if policy_type == "block-all-ingress":
        policy = client.V1NetworkPolicy(
            metadata=client.V1ObjectMeta(
                name=policy_name,
                namespace=namespace
            ),
            spec=client.V1NetworkPolicySpec(
                pod_selector=pod_selector,
                policy_types=["Ingress"],
                ingress=[]  # Empty ingress rules = deny all
            )
        )
    
    elif policy_type == "block-all-egress":
        policy = client.V1NetworkPolicy(
            metadata=client.V1ObjectMeta(
                name=policy_name,
                namespace=namespace
            ),
            spec=client.V1NetworkPolicySpec(
                pod_selector=pod_selector,
                policy_types=["Egress"],
                egress=[]  # Empty egress rules = deny all
            )
        )
    
    elif policy_type == "block-all":
        policy = client.V1NetworkPolicy(
            metadata=client.V1ObjectMeta(
                name=policy_name,
                namespace=namespace
            ),
            spec=client.V1NetworkPolicySpec(
                pod_selector=pod_selector,
                policy_types=["Ingress", "Egress"],
                ingress=[],
                egress=[]
            )
        )
    
    elif policy_type == "allow-port" and port:
        # Allow specific port ingress
        port_rule = client.V1NetworkPolicyPort(
            port=int(port),
            protocol="TCP"
        )
        ingress_rule = client.V1NetworkPolicyIngressRule(
            ports=[port_rule]
        )
        policy = client.V1NetworkPolicy(
            metadata=client.V1ObjectMeta(
                name=policy_name,
                namespace=namespace
            ),
            spec=client.V1NetworkPolicySpec(
                pod_selector=pod_selector,
                policy_types=["Ingress"],
                ingress=[ingress_rule]
            )
        )
    
    elif policy_type == "allow-port-range" and port_range:
        # Parse port range (e.g., "8000-8080")
        start_port, end_port = map(int, port_range.split("-"))
        port_rule = client.V1NetworkPolicyPort(
            port=start_port,
            end_port=end_port,
            protocol="TCP"
        )
        ingress_rule = client.V1NetworkPolicyIngressRule(
            ports=[port_rule]
        )
        policy = client.V1NetworkPolicy(
            metadata=client.V1ObjectMeta(
                name=policy_name,
                namespace=namespace
            ),
            spec=client.V1NetworkPolicySpec(
                pod_selector=pod_selector,
                policy_types=["Ingress"],
                ingress=[ingress_rule]
            )
        )
    
    else:
        console.print(f":fire: Unknown network policy type: {policy_type}")
        return None
    
    try:
        network_v1.create_namespaced_network_policy(
            namespace=namespace,
            body=policy
        )
        console.print(f":shield: Created NetworkPolicy: [bold green]{policy_name}[/bold green]")
        return policy_name
    except ApiException as e:
        console.print(f":fire: Failed to create NetworkPolicy: {e.reason}")
        return None


def delete_network_policy(
    namespace: str,
    policy_name: str,
    context: str = None,
) -> bool:
    """delete a NetworkPolicy"""
    
    network_v1 = client.NetworkingV1Api(get_api_client(context))
    
    try:
        network_v1.delete_namespaced_network_policy(
            name=policy_name,
            namespace=namespace
        )
        console.print(f":shield: Deleted NetworkPolicy: [bold red]{policy_name}[/bold red]")
        return True
    except ApiException as e:
        console.print(f":fire: Failed to delete NetworkPolicy: {e.reason}")
        return False


def get_user_identifier() -> str:
    """get current user identifier for session tracking"""
    return getpass.getuser()


def list_debug_sessions(
    namespace: str = None,
    context: str = None,
) -> List[Dict]:
    """list active debug sessions (pods with debug labels)"""
    
    v1 = client.CoreV1Api(get_api_client(context))
    
    try:
        if namespace:
            pods = v1.list_namespaced_pod(
                namespace=namespace,
                label_selector="app=kubectl-application-shell"
            )
        else:
            pods = v1.list_pod_for_all_namespaces(
                label_selector="app=kubectl-application-shell"
            )
    except (ApiException, MaxRetryError) as e:
        console.print(f":fire: Unable to list debug sessions: {e.reason}")
        return []

    sessions = []
    for pod in pods.items:
        labels = pod.metadata.labels or {}
        session_info = {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "user": labels.get("debug-user", "unknown"),
            "deployment": labels.get("debug-deployment", "unknown"),
            "created": pod.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") if pod.metadata.creation_timestamp else "unknown",
            "node": pod.spec.node_name or "pending"
        }
        sessions.append(session_info)
    
    return sessions


def get_debug_session(
    session_name: str,
    namespace: str,
    context: str = None,
) -> Optional[Dict]:
    """get details for a specific debug session"""
    
    v1 = client.CoreV1Api(get_api_client(context))
    
    try:
        pod = v1.read_namespaced_pod(
            name=session_name,
            namespace=namespace
        )
    except (ApiException, MaxRetryError) as e:
        console.print(f":fire: Unable to get session {session_name}: {e.reason}")
        return None
    
    # Verify it's a debug session
    labels = pod.metadata.labels or {}
    if labels.get("app") != "kubectl-application-shell":
        console.print(f":fire: Pod {session_name} is not a debug session")
        return None
    
    return {
        "name": pod.metadata.name,
        "namespace": pod.metadata.namespace,
        "status": pod.status.phase,
        "user": labels.get("debug-user", "unknown"),
        "deployment": labels.get("debug-deployment", "unknown"),
        "created": pod.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") if pod.metadata.creation_timestamp else "unknown",
        "node": pod.spec.node_name or "pending",
        "container_name": pod.spec.containers[0].name if pod.spec.containers else "unknown"
    }


def terminate_debug_session(
    session_name: str,
    namespace: str,
    context: str = None,
) -> bool:
    """terminate a specific debug session"""
    
    v1 = client.CoreV1Api(get_api_client(context))
    
    # First verify it's a debug session
    session = get_debug_session(session_name, namespace, context)
    if not session:
        return False
    
    # Check if current user owns the session
    current_user = get_user_identifier()
    if session["user"] != current_user:
        console.print(f":fire: Cannot terminate session owned by {session['user']} (you are {current_user})")
        return False
    
    try:
        v1.delete_namespaced_pod(
            name=session_name,
            namespace=namespace
        )
        console.print(f":skull: Terminated debug session: [bold red]{session_name}[/bold red]")
        return True
    except (ApiException, MaxRetryError) as e:
        console.print(f":fire: Failed to terminate session: {e.reason}")
        return False


def resume_debug_session(
    session_name: str,
    namespace: str,
    kubectl_path: Path,
    context: str = None,
    session_log: str = None,
    no_tty: bool = False,
) -> str:
    """generate command to resume a debug session"""
    
    # Verify session exists and get details
    session = get_debug_session(session_name, namespace, context)
    if not session:
        return None
    
    if session["status"] != "Running":
        console.print(f":fire: Session {session_name} is not running (status: {session['status']})")
        return None
    
    # Check if current user owns the session
    current_user = get_user_identifier()
    if session["user"] != current_user:
        console.print(f":fire: Cannot resume session owned by {session['user']} (you are {current_user})")
        return None
    
    # Build kubectl exec command
    interactive_flags = "-it" if not no_tty else "-i"
    container_name = session["container_name"]
    
    cmd_parts = [
        f"{kubectl_path} exec {interactive_flags} --namespace={namespace} ",
        f"--context={context} " if context else " ",
        f"{session_name} ",
        f"--container={container_name} -- /bin/bash"
    ]
    
    base_cmd = "".join(cmd_parts)
    
    # Add session logging if specified
    if session_log:
        cmd = f"script -q {session_log} -c \"{base_cmd}\""
        console.print(f":memo: Session will be logged to [bold green]{session_log}[/bold green]")
    else:
        cmd = base_cmd
    
    return cmd
