from typing import Dict, Optional

from django.core.handlers.asgi import ASGIRequest
from django.db import transaction
from django.http import HttpResponse
from django.urls import path

from haupt.common.endpoints.validation import validate_methods
from haupt.streams.controllers.k8s_crd import get_k8s_operation
from haupt.streams.controllers.k8s_pods import get_pods
from haupt.streams.endpoints.base import UJSONResponse
from polyaxon import settings
from polyaxon.k8s.manager.async_manager import AsyncK8sManager
from polyaxon.utils.fqn_utils import get_resource_name_for_kind


@transaction.non_atomic_requests
async def k8s_inspect(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    project: str,
    run_uuid: str,
    methods: Optional[Dict] = None,
) -> HttpResponse:
    validate_methods(request, methods)
    resource_name = get_resource_name_for_kind(run_uuid=run_uuid)
    k8s_manager = AsyncK8sManager(
        namespace=namespace,
        in_cluster=settings.CLIENT_CONFIG.in_cluster,
    )
    await k8s_manager.setup()
    k8s_operation = await get_k8s_operation(
        k8s_manager=k8s_manager, resource_name=resource_name
    )
    data = None
    if k8s_operation:
        data = await get_pods(k8s_manager=k8s_manager, run_uuid=run_uuid)
    if k8s_manager:
        await k8s_manager.close()
    return UJSONResponse(data or {})


URLS_RUNS_K8S_INSPECT = (
    "<str:namespace>/<str:owner>/<str:project>/runs/<str:run_uuid>/k8s_inspect"
)

# fmt: off
k8s_routes = [
    path(
        URLS_RUNS_K8S_INSPECT,
        k8s_inspect,
        name="k8s_inspect",
        kwargs=dict(methods=["GET"]),
    ),
]
