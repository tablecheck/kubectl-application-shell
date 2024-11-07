"""support functions for kubectl-application-shell"""

from kubernetes import client
from kubernetes.client.rest import ApiException


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
