from typing import List, Tuple
from urllib.parse import urlparse

from rest_framework import status

from django.http import HttpResponse

from polyaxon import settings
from polyaxon._k8s.manager.async_manager import AsyncK8sManager
from polyaxon.api import K8S_V1_LOCATION


def _check_exec(namespace: str, uri_path: List[str], query_params: str):
    pod, container = uri_path
    query_params += "&container={}".format(container)
    path = "api/v1/namespaces/{namespace}/pods/{pod}/exec".format(
        namespace=namespace,
        pod=pod,
    )
    return path, query_params


VALIDATION_PATHS = {
    "k8s_exec": _check_exec,
}


def k8s_check(uri: str) -> Tuple[str, str]:
    parsed_uri = urlparse(uri)
    uri_path = parsed_uri.path.split(K8S_V1_LOCATION)[-1].split("/")
    path_to_check = None
    for vpath in VALIDATION_PATHS:
        if vpath in uri_path:
            path_to_check = vpath
    if not path_to_check:
        raise ValueError("A valid k8s path param is required")
    start = uri_path.index(path_to_check) + 1
    data = uri_path[start:]
    namespace = uri_path[0]
    return VALIDATION_PATHS[path_to_check](namespace, data, parsed_uri.query)


async def reverse_k8s(path) -> HttpResponse:
    if not path:
        return HttpResponse(
            content="A valid k8s path param is required",
            status=status.HTTP_400_BAD_REQUEST,
        )
    config = await AsyncK8sManager.load_config(
        in_cluster=settings.CLIENT_CONFIG.in_cluster
    )
    config_auth = AsyncK8sManager.get_config_auth(config)
    return HttpResponse(
        status=status.HTTP_200_OK,
        headers={
            "K8S_URI": "{}/{}".format(config.host, path),
            "K8S_TOKEN": config_auth,
        },
    )
