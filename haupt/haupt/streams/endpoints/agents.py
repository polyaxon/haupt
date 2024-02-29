import logging

from typing import Dict, List, Optional, Union

from clipped.utils.bools import to_bool
from rest_framework import status

from django.core.handlers.asgi import ASGIRequest
from django.db import transaction
from django.http import HttpResponse
from django.urls import path

from haupt.common.endpoints.files import FilePathResponse
from haupt.common.endpoints.validation import validate_internal_auth, validate_methods
from haupt.streams.connections.fs import AppFS
from haupt.streams.controllers.logs import get_archived_agent_logs
from haupt.streams.endpoints.base import UJSONResponse
from haupt.streams.tasks.op_spec import download_agent_spec, upload_agent_spec
from kubernetes_asyncio.client import V1Pod
from polyaxon import settings
from polyaxon._fs.async_manager import upload_data
from polyaxon._k8s.logging.async_monitor import (
    collect_agent_service_logs,
    get_agent_spec,
)
from polyaxon._k8s.manager.async_manager import AsyncK8sManager
from polyaxon._services import PolyaxonServices
from traceml.logging import V1Logs

logger = logging.getLogger("haupt.streams.agents")


@transaction.non_atomic_requests
async def collect_agent_data(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    agent_uuid: str,
    methods: Optional[Dict] = None,
) -> Union[HttpResponse, FilePathResponse]:
    validate_methods(request, methods)
    try:
        validate_internal_auth(request)
    except Exception as e:
        errors = "Request requires an authenticated internal service %s" % e
        logger.warning(errors)
        return UJSONResponse(
            data={"errors": errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    fs = await AppFS.get_fs()
    store_path = AppFS.get_fs_root_path()

    async def collect_and_archive_agent_services_logs(pods: List[V1Pod]):
        for pod in pods:
            logs = await collect_agent_service_logs(k8s_manager=k8s_manager, pod=pod)

            for service in [
                PolyaxonServices.STREAMS.value,
                PolyaxonServices.OPERATOR.value,
                PolyaxonServices.AGENT.value,
            ]:
                if service in pod.metadata.name:
                    break
            if not service:
                continue

            last_file = 0
            for c_logs in V1Logs.chunk_logs(logs):
                last_file += 1
                subpath = ".agents/{}/logs/{}/{}".format(agent_uuid, service, last_file)
                await upload_data(
                    fs=fs, store_path=store_path, subpath=subpath, data=c_logs.to_json()
                )

    k8s_manager = AsyncK8sManager(
        namespace=namespace,
        in_cluster=settings.CLIENT_CONFIG.in_cluster,
    )
    await k8s_manager.setup()

    agent_spec, pods, _ = await get_agent_spec(k8s_manager=k8s_manager)
    if agent_spec:
        await upload_agent_spec(
            fs=fs,
            store_path=store_path,
            agent_uuid=agent_uuid,
            agent_spec=agent_spec,
        )
    if pods:
        await collect_and_archive_agent_services_logs(pods=pods)

    if k8s_manager:
        await k8s_manager.close()
    return UJSONResponse({})


@transaction.non_atomic_requests
async def k8s_inspect_agent(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    agent_uuid: str,
    methods: Optional[Dict] = None,
) -> Union[HttpResponse, FilePathResponse]:
    validate_methods(request, methods)
    connection = request.GET.get("connection")

    spec_path = await download_agent_spec(
        fs=await AppFS.get_fs(connection=connection),
        store_path=AppFS.get_fs_root_path(connection=connection),
        agent_uuid=agent_uuid,
    )
    if spec_path:
        return FilePathResponse(filepath=spec_path)
    return UJSONResponse({})


@transaction.non_atomic_requests
async def get_agent_logs(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    agent_uuid: str,
    methods: Optional[Dict] = None,
) -> UJSONResponse:
    validate_methods(request, methods)
    force = to_bool(request.GET.get("force"), handle_none=True)
    connection = request.GET.get("connection")
    service = request.GET.get("service")
    last_file = request.GET.get("last_file")

    operation_logs, last_file, files = await get_archived_agent_logs(
        fs=await AppFS.get_fs(connection=connection),
        store_path=AppFS.get_fs_root_path(connection=connection),
        agent_uuid=agent_uuid,
        service=service,
        last_file=last_file,
        check_cache=not force,
    )
    data = dict(
        last_time=None,
        last_file=last_file,
        logs=operation_logs,
        files=files,
    )
    return UJSONResponse(data)


URLS_AGENTS_COLLECT = "<str:namespace>/<str:owner>/agents/<str:agent_uuid>/collect"
URLS_AGENTS_K8S_INSPECT = (
    "<str:namespace>/<str:owner>/agents/<str:agent_uuid>/k8s_inspect"
)
URLS_AGENTS_LOGS = "<str:namespace>/<str:owner>/agents/<str:agent_uuid>/logs"


# fmt: off
internal_agent_routes = [
    path(
        URLS_AGENTS_COLLECT,
        collect_agent_data,
        name="collect_agent_data",
        kwargs=dict(methods=["POST"]),
    ),
]
agent_routes = [
    path(
        URLS_AGENTS_K8S_INSPECT,
        k8s_inspect_agent,
        name="k8s_inspect_agent",
        kwargs=dict(methods=["GET"]),
    ),
    path(
        URLS_AGENTS_LOGS,
        get_agent_logs,
        name="get_agent_logs",
        kwargs=dict(methods=["GET"]),
    ),
]
