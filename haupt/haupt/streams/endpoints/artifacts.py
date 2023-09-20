from typing import Dict, Optional, Union

from clipped.utils.bools import to_bool
from clipped.utils.json import orjson_loads
from rest_framework import status

from django.core.handlers.asgi import ASGIRequest
from django.db import transaction
from django.http import FileResponse, HttpResponse
from django.urls import path

from haupt.common.endpoints.files import FilePathResponse
from haupt.common.endpoints.validation import validate_methods
from haupt.streams.connections.fs import AppFS
from haupt.streams.controllers.notebooks import render_notebook
from haupt.streams.controllers.uploads import handle_posted_data
from haupt.streams.endpoints.base import UJSONResponse
from haupt.streams.endpoints.utils import redirect_file
from polyaxon._fs.async_manager import (
    check_is_file,
    delete_file_or_dir,
    download_dir,
    download_file,
    list_files,
)


async def handle_upload(
    request: ASGIRequest, run_uuid: str, is_file: bool
) -> HttpResponse:
    content_file = request.FILES["upload_file"]
    content_json = request.POST.get("json")
    content_json = orjson_loads(content_json) if content_json else {}
    overwrite = content_json.get("overwrite", True)
    untar = content_json.get("untar", True)
    path = content_json.get("path", "")
    connection = content_json.get("connection")
    try:
        archived_path = await handle_posted_data(
            fs=await AppFS.get_fs(connection=connection),
            store_path=AppFS.get_fs_root_path(connection=connection),
            content_file=content_file,
            root_path=run_uuid,
            path=path,
            upload=True,
            is_file=is_file,
            overwrite=overwrite,
            untar=untar,
        )
    except Exception as e:
        return HttpResponse(
            content="Run's artifacts upload was unsuccessful, "
            "an error was raised while uploading the data %s." % e,
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not archived_path:
        return HttpResponse(
            content="Artifact not found and not uploaded: filepath={}".format(
                archived_path
            ),
            status=status.HTTP_404_NOT_FOUND,
        )
    return HttpResponse(status=status.HTTP_200_OK)


def clean_path(filepath: str):
    return filepath.strip("/")


@transaction.non_atomic_requests
async def handle_artifact(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    project: str,
    run_uuid: str,
    methods: Optional[Dict] = None,
) -> HttpResponse:
    validate_methods(request, methods)
    if request.method == "GET":
        return await download_artifact(request, run_uuid=run_uuid)
    if request.method == "DELETE":
        return await delete_artifact(request, run_uuid=run_uuid)
    if request.method == "POST":
        return await upload_artifact(request, run_uuid=run_uuid)


@transaction.non_atomic_requests
async def ro_artifact(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    project: str,
    run_uuid: str,
    path: str,
    methods: Optional[Dict] = None,
) -> HttpResponse:
    validate_methods(request, methods)
    return await download_artifact(request, run_uuid, path, True)


async def download_artifact(
    request: ASGIRequest,
    run_uuid: str,
    path: Optional[str] = None,
    stream: Optional[bool] = None,
) -> Union[HttpResponse, FileResponse]:
    filepath = request.GET.get("path", path or "")
    stream = to_bool(request.GET.get("stream", stream), handle_none=True)
    force = to_bool(request.GET.get("force"), handle_none=True)
    render = to_bool(request.GET.get("render"), handle_none=True)
    connection = request.GET.get("connection")
    if not filepath:
        return HttpResponse(
            content="A `path` query param is required to stream a file content",
            status=status.HTTP_400_BAD_REQUEST,
        )
    if render and not filepath.endswith(".ipynb"):
        return HttpResponse(
            content="Artifact with 'filepath={}' does not have a valid extension.".format(
                filepath
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )
    subpath = "{}/{}".format(run_uuid, clean_path(filepath)).rstrip("/")
    archived_path = await download_file(
        fs=await AppFS.get_fs(connection=connection),
        store_path=AppFS.get_fs_root_path(connection=connection),
        subpath=subpath,
        check_cache=not force,
    )
    if not archived_path:
        return HttpResponse(
            content="Artifact not found: filepath={}".format(archived_path),
            status=status.HTTP_404_NOT_FOUND,
        )
    if stream:
        if render:
            archived_path = await render_notebook(
                archived_path=archived_path, check_cache=not force
            )
        return FilePathResponse(filepath=archived_path)
    return await redirect_file(archived_path)


async def upload_artifact(request: ASGIRequest, run_uuid: str) -> HttpResponse:
    return await handle_upload(request=request, run_uuid=run_uuid, is_file=True)


async def delete_artifact(request: ASGIRequest, run_uuid: str) -> HttpResponse:
    filepath = request.GET.get("path", "")
    if not filepath:
        return HttpResponse(
            content="A `path` query param is required to delete a file",
            status=status.HTTP_400_BAD_REQUEST,
        )
    subpath = "{}/{}".format(run_uuid, clean_path(filepath)).rstrip("/")
    connection = request.GET.get("connection")
    is_deleted = await delete_file_or_dir(
        fs=await AppFS.get_fs(connection=connection),
        store_path=AppFS.get_fs_root_path(connection=connection),
        subpath=subpath,
        is_file=True,
    )
    if not is_deleted:
        return HttpResponse(
            content="Artifact could not be deleted: filepath={}".format(subpath),
            status=status.HTTP_400_BAD_REQUEST,
        )
    return HttpResponse(
        status=status.HTTP_204_NO_CONTENT,
    )


@transaction.non_atomic_requests
async def handle_artifacts(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    project: str,
    run_uuid: str,
    methods: Optional[Dict] = None,
) -> HttpResponse:
    validate_methods(request, methods)
    if request.method == "GET":
        return await download_artifacts(request, run_uuid=run_uuid)
    if request.method == "DELETE":
        return await delete_artifacts(request, run_uuid=run_uuid)
    if request.method == "POST":
        return await upload_artifacts(request, run_uuid=run_uuid)


async def download_artifacts(request: ASGIRequest, run_uuid: str) -> HttpResponse:
    check_path = to_bool(request.GET.get("check_path"), handle_none=True)
    if not check_path:
        # Backwards compatibility
        check_path = to_bool(request.GET.get("check_file"), handle_none=True)
    path = request.GET.get("path", "")
    connection = request.GET.get("connection")
    subpath = "{}/{}".format(run_uuid, clean_path(path)).rstrip("/")
    fs = await AppFS.get_fs(connection=connection)
    store_path = AppFS.get_fs_root_path(connection=connection)
    if check_path:
        is_file = await check_is_file(fs=fs, store_path=store_path, subpath=subpath)
        if is_file:
            return await download_artifact(request, run_uuid=run_uuid)
    archived_path = await download_dir(
        fs=fs, store_path=store_path, subpath=subpath, to_tar=True
    )
    if not archived_path:
        return HttpResponse(
            content="Artifact not found: filepath={}".format(archived_path),
            status=status.HTTP_404_NOT_FOUND,
        )
    return await redirect_file(archived_path)


async def upload_artifacts(request: ASGIRequest, run_uuid: str) -> HttpResponse:
    return await handle_upload(request=request, run_uuid=run_uuid, is_file=False)


async def delete_artifacts(request: ASGIRequest, run_uuid: str) -> HttpResponse:
    path = request.GET.get("path", "")
    connection = request.GET.get("connection")
    subpath = "{}/{}".format(run_uuid, clean_path(path)).rstrip("/")
    is_deleted = await delete_file_or_dir(
        fs=await AppFS.get_fs(connection=connection),
        store_path=AppFS.get_fs_root_path(connection=connection),
        subpath=subpath,
        is_file=False,
    )
    if not is_deleted:
        return HttpResponse(
            content="Artifacts could not be deleted: filepath={}".format(subpath),
            status=status.HTTP_400_BAD_REQUEST,
        )
    return HttpResponse(
        status=status.HTTP_204_NO_CONTENT,
    )


@transaction.non_atomic_requests
async def tree_artifacts(
    request: ASGIRequest,
    namespace: str,
    owner: str,
    project: str,
    run_uuid: str,
    methods: Optional[Dict] = None,
) -> UJSONResponse:
    validate_methods(request, methods)
    filepath = request.GET.get("path", "")
    connection = request.GET.get("connection")
    ls = await list_files(
        fs=await AppFS.get_fs(connection=connection),
        store_path=AppFS.get_fs_root_path(connection=connection),
        subpath=run_uuid,
        filepath=clean_path(filepath),
        force=True,
    )
    return UJSONResponse(ls)


URLS_RUNS_ARTIFACT = (
    "<str:namespace>/<str:owner>/<str:project>/runs/<str:run_uuid>/artifact"
)
URLS_RUNS_EMBEDDED_ARTIFACT = (
    "<str:namespace>/<str:owner>/<str:project>/runs/<str:run_uuid>/embedded_artifact"
)
URLS_RUNS_RO_ARTIFACT = "<str:namespace>/<str:owner>/<str:project>/runs/<str:run_uuid>/ro_artifact/<path:path>"
URLS_RUNS_ARTIFACTS = (
    "<str:namespace>/<str:owner>/<str:project>/runs/<str:run_uuid>/artifacts"
)
URLS_RUNS_ARTIFACTS_TREE = (
    "<str:namespace>/<str:owner>/<str:project>/runs/<str:run_uuid>/artifacts/tree"
)

# fmt: off
artifacts_routes = [
    path(
        URLS_RUNS_ARTIFACT,
        handle_artifact,
        name="artifact",
        kwargs=dict(methods=["GET", "DELETE", "POST"]),
    ),
    path(
        URLS_RUNS_EMBEDDED_ARTIFACT,
        handle_artifact,
        name="download_embedded_artifact",
        kwargs=dict(methods=["GET"]),
    ),
    path(
        URLS_RUNS_RO_ARTIFACT,
        ro_artifact,
        name="read_only_artifact",
        kwargs=dict(methods=["GET"]),
    ),
    path(
        URLS_RUNS_ARTIFACTS,
        handle_artifacts,
        name="download_artifacts",
        kwargs=dict(methods=["GET", "DELETE", "POST"]),
    ),
    path(
        URLS_RUNS_ARTIFACTS_TREE,
        tree_artifacts,
        name="list_artifacts",
        kwargs=dict(methods=["GET"]),
    ),
]
