#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import os

from rest_framework import status

from django.core.handlers.asgi import ASGIRequest
from django.http import HttpResponse

from asgiref.sync import sync_to_async
from polyaxon import settings
from polyaxon.constants.globals import DEFAULT_UPLOADS_PATH
from polyaxon.fs.async_manager import upload_dir, upload_file
from polyaxon.fs.types import FSSystem
from polyaxon.lifecycle import V1ProjectFeature
from polyaxon.utils.path_utils import check_or_create_path, delete_path, untar_file


async def handle_posted_data(
    fs: FSSystem,
    content_file: any,
    root_path: str,
    path: str,
    upload: bool,
    is_file: bool,
    overwrite: bool = True,
    untar: bool = True,
) -> str:
    filename = content_file.name
    tmp_path = "{}/{}".format(root_path, os.path.basename(filename)).rstrip("/")
    if path:
        root_path = "{}/{}".format(root_path, path).rstrip("/")
        if is_file:
            root_path = "{}/{}".format(root_path, os.path.basename(filename))
    else:
        if untar:
            root_path = "{}/{}".format(root_path, DEFAULT_UPLOADS_PATH).rstrip("/")
        else:
            root_path = tmp_path
    if not untar:
        tmp_path = root_path

    full_tmppath = settings.AGENT_CONFIG.get_local_path(
        subpath=tmp_path, entity=V1ProjectFeature.RUNTIME
    )
    full_filepath = settings.AGENT_CONFIG.get_local_path(
        subpath=root_path, entity=V1ProjectFeature.RUNTIME
    )

    if overwrite and os.path.exists(full_filepath):
        delete_path(full_filepath)
    if not overwrite and os.path.exists(full_filepath):
        return full_filepath
    # Always clean tmp path
    if overwrite and os.path.exists(full_tmppath):
        delete_path(full_tmppath)

    check_or_create_path(full_tmppath, is_dir=False)
    check_or_create_path(full_filepath, is_dir=not is_file)

    # Creating the new file
    with open(full_tmppath, "wb") as destination:
        for chunk in content_file.chunks():
            destination.write(chunk)
    if untar:
        await sync_to_async(untar_file)(
            full_tmppath, extract_path=full_filepath, use_filepath=False
        )
    if upload:
        if is_file:
            await upload_file(fs=fs, subpath=root_path)
        else:
            await upload_dir(fs=fs, subpath=root_path)
    return root_path


async def handle_upload(
    fs: FSSystem, request: ASGIRequest, run_uuid: str, is_file: bool
) -> HttpResponse:
    content_file = request.FILES["upload_file"]
    overwrite = request.POST.get("overwrite", True)
    untar = request.POST.get("untar", True)
    path = request.POST.get("path", "")
    try:
        archived_path = await handle_posted_data(
            fs=fs,
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
            detail="Run's artifacts upload was unsuccessful, "
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
