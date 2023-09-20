import os

from clipped.utils.paths import check_or_create_path, delete_path, untar_file

from asgiref.sync import sync_to_async
from polyaxon import settings
from polyaxon._fs.async_manager import upload_dir, upload_file
from polyaxon._fs.types import FSSystem
from polyaxon._fs.utils import get_store_path
from polyaxon.schemas import V1ProjectFeature


async def handle_posted_data(
    fs: FSSystem,
    store_path: str,
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
            root_path = "{}/{}".format(root_path, path or "/").rstrip("/")
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
    store_full_path = get_store_path(
        store_path=store_path, subpath=root_path, entity=V1ProjectFeature.RUNTIME
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
    if upload and store_full_path != full_filepath:
        if is_file:
            await upload_file(fs=fs, store_path=store_path, subpath=root_path)
        else:
            await upload_dir(fs=fs, store_path=store_path, subpath=root_path)
    return root_path
