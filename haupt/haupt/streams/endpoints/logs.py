#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
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
from polyaxon import settings
from polyaxon.k8s.async_manager import AsyncK8SManager
from polyaxon.k8s.logging.async_monitor import query_k8s_operation_logs
from polyaxon.utils.fqn_utils import get_resource_name, get_resource_name_for_kind

logger = logging.getLogger("polyaxon.streams.logs")


@transaction.non_atomic_requests
async def get_logs(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    project: str,
    run_uuid: str,
    methods: Optional[Dict] = None,
) -> UJSONResponse:
    validate_methods(request, methods)
    force = to_bool(request.GET.get("force"), handle_none=True)
    last_time = request.GET.get("last_time")
    if last_time:
        last_time = parse_datetime(last_time).astimezone()
    last_file = request.GET.get("last_file")
    files = []

    if last_time:
        resource_name = get_resource_name(run_uuid=run_uuid)

        k8s_manager = AsyncK8SManager(
            namespace=settings.CLIENT_CONFIG.namespace,
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
                fs=await AppFS.get_fs(), run_uuid=run_uuid, last_time=last_time
            )
        if k8s_manager:
            await k8s_manager.close()

    else:
        operation_logs, last_file, files = await get_archived_operation_logs(
            fs=await AppFS.get_fs(),
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
async def collect_logs(
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
        return UJSONResponse(
            data={
                "errors": "Request requires an authenticated internal service %s" % e
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    resource_name = get_resource_name_for_kind(run_uuid=run_uuid, run_kind=run_kind)
    k8s_manager = AsyncK8SManager(
        namespace=settings.CLIENT_CONFIG.namespace,
        in_cluster=settings.CLIENT_CONFIG.in_cluster,
    )
    await k8s_manager.setup()
    k8s_operation = await get_k8s_operation(
        k8s_manager=k8s_manager, resource_name=resource_name
    )
    if not k8s_operation:
        errors = "Run's logs was not collected, resource was not found."
        logger.warning(errors)
        return UJSONResponse(
            data={"errors": errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    operation_logs, _ = await query_k8s_operation_logs(
        instance=run_uuid, k8s_manager=k8s_manager, last_time=None
    )
    if k8s_manager:
        await k8s_manager.close()
    if not operation_logs:
        return HttpResponse(
            content={"errors": "Operation logs could not be fetched"},
            status=status.HTTP_404_NOT_FOUND,
        )

    fs = await AppFS.get_fs()
    try:
        await upload_logs(fs=fs, run_uuid=run_uuid, logs=operation_logs)
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
    if settings.AGENT_CONFIG.is_replica:
        try:
            await clean_tmp_logs(fs=fs, run_uuid=run_uuid)
        except Exception as e:
            return HttpResponse(
                content="Logs collection failed. Error: %s" % e,
                status=status.HTTP_400_BAD_REQUEST,
            )
        return HttpResponse(status=status.HTTP_200_OK)
    return HttpResponse(status=status.HTTP_200_OK)


URLS_RUNS_COLLECT_LOGS = (
    "<str:namespace>/<str:owner>/<str:project>/runs/<str:run_uuid>/<str:run_kind>/logs"
)
URLS_RUNS_LOGS = "<str:namespace>/<str:owner>/<str:project>/runs/<str:run_uuid>/logs"


# fmt: off
logs_routes = [
    path(
        URLS_RUNS_LOGS,
        get_logs,
        name="logs",
        kwargs=dict(methods=["GET"]),
    ),
]
internal_logs_routes = [
    path(
        URLS_RUNS_COLLECT_LOGS,
        collect_logs,
        name="collect_logs",
        kwargs=dict(methods=["POST"]),
    ),
]
