import os

from typing import Dict, Optional

from rest_framework import status

from django.core.handlers.asgi import ASGIRequest
from django.http import HttpResponse
from django.urls import path, re_path

from haupt import settings
from haupt.common.apis.urls import versions
from haupt.common.apis.version import get_version
from haupt.common.endpoints.validation import validate_methods
from haupt.streams.endpoints.base import ConfigResponse, UJSONResponse
from polyaxon._contexts import paths as ctx_paths
from polyaxon.schemas import V1ProjectFeature

VIEWER_KEY = "b4242c3566df410dacec2299660d1f47"


async def get_run_details(
    request: ASGIRequest,
    owner: str,
    project: str,
    run_uuid: str,
    methods: Optional[Dict] = None,
) -> HttpResponse:
    validate_methods(request, methods)
    subpath = os.path.join(run_uuid, ctx_paths.CONTEXT_LOCAL_RUN)
    data_path = settings.SANDBOX_CONFIG.get_store_path(
        subpath=subpath, entity=V1ProjectFeature.RUNTIME
    )
    if not os.path.exists(data_path) or not os.path.isfile(data_path):
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    with open(data_path, "r") as config_file:
        config_str = config_file.read()
    return ConfigResponse(config_str)


async def get_run_artifact_lineage(
    request: ASGIRequest,
    owner: str,
    project: str,
    run_uuid: str,
    methods: Optional[Dict] = None,
) -> HttpResponse:
    validate_methods(request, methods)
    subpath = os.path.join(run_uuid, ctx_paths.CONTEXT_LOCAL_LINEAGES)
    data_path = settings.SANDBOX_CONFIG.get_store_path(
        subpath=subpath, entity=V1ProjectFeature.RUNTIME
    )
    if not os.path.exists(data_path) or not os.path.isfile(data_path):
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    with open(data_path, "r") as config_file:
        config_str = config_file.read()
        config_str = f'{{"results": {config_str}}}'

    return ConfigResponse(config_str)


async def list_runs(
    request: ASGIRequest, owner: str, project: str, methods: Optional[Dict] = None
) -> HttpResponse:
    validate_methods(request, methods)
    # project = request.path_params["project"]
    data_path = settings.SANDBOX_CONFIG.get_store_path(
        subpath="", entity=V1ProjectFeature.RUNTIME
    )
    if not os.path.exists(data_path) or not os.path.isdir(data_path):
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    data = []
    for run in os.listdir(data_path):
        run_path = os.path.join(data_path, run, ctx_paths.CONTEXT_LOCAL_RUN)
        if not os.path.exists(run_path) or not os.path.isfile(run_path):
            continue

        with open(run_path, "r") as config_file:
            data.append(config_file.read())
    data_str = ",".join(data)
    config_str = f'{{"results": [{data_str}], "count": {len(data)}}}'
    return ConfigResponse(config_str)


async def get_project_details(
    request: ASGIRequest,
    owner: str,
    project: str,
    methods: Optional[Dict] = None,
) -> HttpResponse:
    validate_methods(request, methods)
    data_path = settings.SANDBOX_CONFIG.get_store_path(
        subpath=project, entity="project"
    )
    if not os.path.exists(data_path) or not os.path.isdir(data_path):
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    data_path = os.path.join(data_path, ctx_paths.CONTEXT_LOCAL_PROJECT)
    if os.path.exists(data_path) and os.path.isfile(data_path):
        with open(data_path, "r") as config_file:
            config_str = config_file.read()
        return ConfigResponse(config_str)

    # Use basic project configuration
    return UJSONResponse({"name": project})


async def list_projects(
    request: ASGIRequest, owner: str, methods: Optional[Dict] = None
) -> HttpResponse:
    validate_methods(request, methods)
    data_path = settings.SANDBOX_CONFIG.get_store_path(subpath="", entity="project")
    if not os.path.exists(data_path) or not os.path.isdir(data_path):
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    data = []
    for proj in os.listdir(data_path):
        data_path = os.path.join(data_path, proj, ctx_paths.CONTEXT_LOCAL_PROJECT)
        if os.path.exists(data_path) and os.path.isfile(data_path):
            with open(data_path, "r") as config_file:
                data.append(config_file.read())
        else:
            data.append(f'{{"name": "{proj}"}}')

    data_str = ",".join(data)
    config_str = f'{{"results": [{data_str}], "count": {len(data)}}}'
    return ConfigResponse(config_str)


async def get_installation_version(
    request: ASGIRequest, methods: Optional[Dict] = None
) -> HttpResponse:
    validate_methods(request, methods)
    data = get_version()
    if not data["key"]:
        data["key"] = VIEWER_KEY
    return UJSONResponse(get_version())


URLS_RUNS_DETAILS = "<str:owner>/<str:project>/runs/<str:run_uuid>/"
URLS_RUNS_STATUSES = "<str:owner>/<str:project>/runs/<str:run_uuid>/statuses"
URLS_RUNS_LINEAGE_ARTIFACTS = (
    "<str:owner>/<str:project>/runs/<str:run_uuid>/lineage/artifacts"
)
URLS_RUNS_LIST = "<str:owner>/<str:project>/runs/"
URLS_PROJECTS_LIST = "<str:owner>/projects/list"
URLS_PROJECTS_DETAILS = "<str:owner>/<str:project>/"

# fmt: off
viewer_routes = [
    re_path(
        versions.URLS_VERSIONS_INSTALLED,
        get_installation_version,
        name="installation_version",
        kwargs=dict(methods=["GET"]),
    ),
    path(
        URLS_RUNS_DETAILS,
        get_run_details,
        name="run_details",
        kwargs=dict(methods=["GET"]),
    ),
    path(
        URLS_RUNS_STATUSES,
        get_run_details,
        name="run_details",
        kwargs=dict(methods=["GET"]),
    ),
    path(
        URLS_RUNS_LINEAGE_ARTIFACTS,
        get_run_artifact_lineage,
        name="run_artifact_lineage",
        kwargs=dict(methods=["GET"]),
    ),
    path(
        URLS_RUNS_LIST,
        list_runs,
        name="list_runs",
        kwargs=dict(methods=["GET"]),
    ),
    path(
        URLS_PROJECTS_LIST,
        list_projects,
        name="project_details",
        kwargs=dict(methods=["GET"]),
    ),
    path(
        URLS_PROJECTS_DETAILS,
        get_project_details,
        name="project_details",
        kwargs=dict(methods=["GET"]),
    ),
]
