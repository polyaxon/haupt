from typing import Dict, Optional, Set, Union

from clipped.utils.bools import to_bool
from clipped.utils.json import orjson_loads
from rest_framework import status

from django.core.handlers.asgi import ASGIRequest
from django.db import transaction
from django.http import HttpResponse
from django.urls import path

from haupt.common.endpoints.validation import validate_methods
from haupt.streams.connections.fs import AppFS
from haupt.streams.controllers.events import (
    get_archived_operation_events,
    get_archived_operation_events_and_assets,
    get_archived_operation_resources,
    get_archived_operations_events,
)
from haupt.streams.endpoints.base import UJSONResponse
from haupt.streams.endpoints.utils import redirect_file
from traceml.artifacts import V1ArtifactKind
from traceml.events import V1Events
from traceml.processors.importance_processors import calculate_importance_correlation


@transaction.non_atomic_requests
async def get_multi_run_events(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    project: str,
    event_kind: str,
    methods: Optional[Dict] = None,
) -> Union[UJSONResponse, HttpResponse]:
    validate_methods(request, methods)
    force = to_bool(request.GET.get("force"), handle_none=True)
    if event_kind not in V1ArtifactKind.to_set():
        return HttpResponse(
            content="received an unrecognisable event {}.".format(event_kind),
            status=status.HTTP_400_BAD_REQUEST,
        )
    run_uuids = request.GET["runs"]
    event_names = request.GET["names"]
    orient = request.GET.get("orient")
    sample = request.GET.get("sample")
    connection = request.GET.get("connection")
    orient = orient or V1Events.ORIENT_DICT
    event_names = {e for e in event_names.split(",") if e} if event_names else set([])
    run_uuids = {e for e in run_uuids.split(",") if e} if run_uuids else set([])
    events = await get_archived_operations_events(
        fs=await AppFS.get_fs(connection=connection),
        store_path=AppFS.get_fs_root_path(connection=connection),
        run_uuids=run_uuids,
        event_kind=event_kind,
        event_names=event_names,
        orient=orient,
        check_cache=not force,
        sample=sample,
    )
    return UJSONResponse({"data": events})


async def get_package_event_assets(
    run_uuid: str, event_kind: str, event_names: Set[str], force: bool, connection: str
) -> HttpResponse:
    archived_path = await get_archived_operation_events_and_assets(
        fs=await AppFS.get_fs(connection=connection),
        store_path=AppFS.get_fs_root_path(connection=connection),
        run_uuid=run_uuid,
        event_kind=event_kind,
        event_names=event_names,
        check_cache=not force,
    )
    if not archived_path:
        return HttpResponse(
            content="Artifact not found: filepath={}".format(archived_path),
            status=status.HTTP_404_NOT_FOUND,
        )
    return await redirect_file(archived_path)


@transaction.non_atomic_requests
async def get_run_events(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    project: str,
    run_uuid: str,
    event_kind: str,
    methods: Optional[Dict] = None,
) -> Union[UJSONResponse, HttpResponse]:
    validate_methods(request, methods)
    force = to_bool(request.GET.get("force"), handle_none=True)
    pkg_assets = to_bool(request.GET.get("pkg_assets"), handle_none=True)
    if event_kind not in V1ArtifactKind.to_set():
        return HttpResponse(
            content="received an unrecognisable event {}.".format(event_kind),
            status=status.HTTP_400_BAD_REQUEST,
        )
    event_names = request.GET["names"]
    orient = request.GET.get("orient")
    sample = request.GET.get("sample")
    connection = request.GET.get("connection")
    orient = orient or V1Events.ORIENT_DICT
    event_names = {e for e in event_names.split(",") if e} if event_names else set([])
    if pkg_assets:
        return await get_package_event_assets(
            run_uuid=run_uuid,
            event_kind=event_kind,
            event_names=event_names,
            force=force,
            connection=connection,
        )
    events = await get_archived_operation_events(
        fs=await AppFS.get_fs(connection=connection),
        store_path=AppFS.get_fs_root_path(connection=connection),
        run_uuid=run_uuid,
        event_kind=event_kind,
        event_names=event_names,
        orient=orient,
        check_cache=not force,
        sample=sample,
    )
    return UJSONResponse({"data": events})


@transaction.non_atomic_requests
async def get_run_resources(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    project: str,
    run_uuid: str,
    methods: Optional[Dict] = None,
) -> UJSONResponse:
    validate_methods(request, methods)
    event_names = request.GET.get("names")
    orient = request.GET.get("orient")
    force = to_bool(request.GET.get("force"), handle_none=True)
    sample = request.GET.get("sample")
    connection = request.GET.get("connection")
    orient = orient or V1Events.ORIENT_DICT
    event_names = {e for e in event_names.split(",") if e} if event_names else set([])
    events = await get_archived_operation_resources(
        fs=await AppFS.get_fs(connection=connection),
        store_path=AppFS.get_fs_root_path(connection=connection),
        run_uuid=run_uuid,
        event_kind=V1ArtifactKind.METRIC,
        event_names=event_names,
        orient=orient,
        check_cache=not force,
        sample=sample,
    )
    return UJSONResponse({"data": events})


@transaction.non_atomic_requests
async def get_run_importance_correlation(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    project: str,
    methods: Optional[Dict] = None,
) -> UJSONResponse:
    validate_methods(request, methods)
    data = orjson_loads(request.body) if request.body else {}
    params = data.get("params")
    metrics = data.get("metrics")
    return UJSONResponse(
        {"data": calculate_importance_correlation(metrics=metrics, params=params)}
    )


URLS_RUNS_MULTI_EVENTS = (
    "<str:namespace>/<str:owner>/<str:project>/runs/multi/events/<str:event_kind>"
)
URLS_RUNS_EVENTS = "<str:namespace>/<str:owner>/<str:project>/runs/<str:run_uuid>/events/<str:event_kind>"
URLS_RUNS_RESOURCES = (
    "<str:namespace>/<str:owner>/<str:project>/runs/<str:run_uuid>/resources"
)
URLS_RUNS_IMPORTANCE_CORRELATION = (
    "<str:namespace>/<str:owner>/<str:project>/runs/multi/importance"
)

# fmt: off
events_routes = [
    path(
        URLS_RUNS_MULTI_EVENTS,
        get_multi_run_events,
        name="multi_run_events",
        kwargs=dict(methods=["GET"]),
    ),
    path(
        URLS_RUNS_RESOURCES,
        get_run_resources,
        name="resources",
        kwargs=dict(methods=["GET"]),
    ),
    path(
        URLS_RUNS_IMPORTANCE_CORRELATION,
        get_run_importance_correlation,
        name="importance",
        kwargs=dict(methods=["POST"]),
    ),
    path(
        URLS_RUNS_EVENTS,
        get_run_events,
        name="events",
        kwargs=dict(methods=["GET"]),
    ),
]
