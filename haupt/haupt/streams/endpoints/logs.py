import logging

from typing import Dict, Optional

from clipped.utils.bools import to_bool
from clipped.utils.dates import parse_datetime
from clipped.utils.serialization import datetime_serialize
from rest_framework import status

from django.core.handlers.asgi import ASGIRequest
from django.db import transaction
from django.http import HttpResponse
from django.urls import path

from haupt.common.endpoints.validation import validate_internal_auth, validate_methods
from haupt.streams.connections.fs import AppFS
from haupt.streams.controllers.k8s_crd import get_k8s_operation
from haupt.streams.controllers.logs import (
    get_archived_operation_logs,
    get_operation_logs,
    get_tmp_operation_logs,
)
from haupt.streams.endpoints.base import UJSONResponse
from haupt.streams.tasks.logs import clean_tmp_logs, upload_logs
from haupt.streams.tasks.op_spec import upload_op_spec
from polyaxon import settings
from polyaxon._k8s.logging.async_monitor import get_op_spec, query_k8s_operation_logs
from polyaxon._k8s.manager.async_manager import AsyncK8sManager
from polyaxon._utils.fqn_utils import get_resource_name, get_resource_name_for_kind

logger = logging.getLogger("haupt.streams.logs")


@transaction.non_atomic_requests
async def get_run_logs(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    project: str,
    run_uuid: str,
    methods: Optional[Dict] = None,
) -> UJSONResponse:
    validate_methods(request, methods)
    force = to_bool(request.GET.get("force"), handle_none=True)
    connection = request.GET.get("connection")
    last_time = request.GET.get("last_time")
    if last_time:
        last_time = parse_datetime(last_time).astimezone()
    last_file = request.GET.get("last_file")
    files = []

    if last_time:
        resource_name = get_resource_name(run_uuid=run_uuid)

        k8s_manager = AsyncK8sManager(
            namespace=namespace,
            in_cluster=settings.CLIENT_CONFIG.in_cluster,
        )
        await k8s_manager.setup()
        k8s_operation = await get_k8s_operation(
            k8s_manager=k8s_manager, resource_name=resource_name
        )
        if k8s_operation:
            operation_logs, last_time = await get_operation_logs(
                k8s_manager=k8s_manager,
                k8s_operation=k8s_operation,
                instance=run_uuid,
                last_time=last_time,
            )
        else:
            operation_logs, last_time = await get_tmp_operation_logs(
                fs=await AppFS.get_fs(connection=connection),
                store_path=AppFS.get_fs_root_path(connection=connection),
                run_uuid=run_uuid,
                last_time=last_time,
            )
        if k8s_manager:
            await k8s_manager.close()

    else:
        operation_logs, last_file, files = await get_archived_operation_logs(
            fs=await AppFS.get_fs(connection=connection),
            store_path=AppFS.get_fs_root_path(connection=connection),
            run_uuid=run_uuid,
            last_file=last_file,
            check_cache=not force,
        )
    data = dict(
        last_time=datetime_serialize(last_time),
        last_file=last_file,
        logs=operation_logs,
        files=files,
    )
    return UJSONResponse(data)


@transaction.non_atomic_requests
async def collect_run_logs(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    project: str,
    run_uuid: str,
    run_kind: str,
    methods: Optional[Dict] = None,
) -> HttpResponse:
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
    resource_name = get_resource_name_for_kind(run_uuid=run_uuid, run_kind=run_kind)
    k8s_manager = AsyncK8sManager(
        namespace=namespace,
        in_cluster=settings.CLIENT_CONFIG.in_cluster,
    )
    await k8s_manager.setup()
    k8s_operation = await get_k8s_operation(
        k8s_manager=k8s_manager, resource_name=resource_name
    )
    if not k8s_operation:
        errors = (
            "Run's logs was not collected, resource was not found for run %s" % run_uuid
        )
        logger.warning(errors)
        return UJSONResponse(
            data={"errors": errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    operation_logs, _ = await query_k8s_operation_logs(
        instance=run_uuid, k8s_manager=k8s_manager, last_time=None
    )
    op_spec, _, _ = await get_op_spec(
        k8s_manager=k8s_manager, run_uuid=run_uuid, run_kind=run_kind
    )
    if k8s_manager:
        await k8s_manager.close()
    if not operation_logs:
        # TODO: Add logic to handle job without logs
        errors = "Operation logs could not be fetched for run %s" % run_uuid
        logger.warning(errors)
        return HttpResponse(
            content={"errors": errors},
            status=status.HTTP_404_NOT_FOUND,
        )

    fs = await AppFS.get_fs()
    store_path = AppFS.get_fs_root_path()
    try:
        await upload_logs(
            fs=fs, store_path=store_path, run_uuid=run_uuid, logs=operation_logs
        )
    except Exception as e:
        errors = (
            "Run's logs was not collected, an error was raised while uploading the data. "
            "Error %s." % e
        )
        logger.warning(errors)
        return UJSONResponse(
            data={"errors": errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        await clean_tmp_logs(fs=fs, store_path=store_path, run_uuid=run_uuid)
    except Exception as e:
        errors = "Did not remove temp logs, an error was raised. " "Error %s." % e
        logger.debug(errors)

    if op_spec:
        try:
            await upload_op_spec(
                fs=fs,
                store_path=store_path,
                run_uuid=run_uuid,
                op_spec=op_spec,
            )
        except Exception as e:
            errors = (
                "Operation spec was not collected, an error was raised while uploading the data. "
                "Error %s." % e
            )
            logger.warning(errors)

    return HttpResponse(status=status.HTTP_200_OK)


URLS_RUNS_COLLECT_LOGS = (
    "<str:namespace>/<str:owner>/<str:project>/runs/<str:run_uuid>/<str:run_kind>/logs"
)
URLS_RUNS_LOGS = "<str:namespace>/<str:owner>/<str:project>/runs/<str:run_uuid>/logs"


# fmt: off
logs_routes = [
    path(
        URLS_RUNS_LOGS,
        get_run_logs,
        name="get_run_logs",
        kwargs=dict(methods=["GET"]),
    ),
]
internal_logs_routes = [
    path(
        URLS_RUNS_COLLECT_LOGS,
        collect_run_logs,
        name="collect_run_logs",
        kwargs=dict(methods=["POST"]),
    ),
]
