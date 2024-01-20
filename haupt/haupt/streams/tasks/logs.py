from datetime import datetime
from typing import List

from clipped.utils.json import orjson_loads
from clipped.utils.paths import delete_path

from asgiref.sync import sync_to_async
from polyaxon._fs.async_manager import (
    delete_file_or_dir,
    download_dir,
    open_file,
    upload_data,
)
from polyaxon._fs.types import FSSystem
from traceml.logging import V1Log, V1Logs


async def clean_tmp_logs(fs: FSSystem, store_path: str, run_uuid: str):
    subpath = "{}/.tmpplxlogs".format(run_uuid)
    delete_path(subpath)
    await delete_file_or_dir(
        fs=fs, store_path=store_path, subpath=subpath, is_file=False
    )


async def upload_logs(fs: FSSystem, store_path: str, run_uuid: str, logs: List[V1Log]):
    for c_logs in V1Logs.chunk_logs(logs):
        last_file = datetime.timestamp(c_logs.logs[-1].timestamp)
        subpath = "{}/plxlogs/{}".format(run_uuid, last_file)
        await upload_data(
            fs=fs, store_path=store_path, subpath=subpath, data=c_logs.to_json()
        )


async def content_to_logs(content, logs_path, to_structured: bool = False):
    if not content:
        return []

    @sync_to_async
    def convert():
        # Version handling
        if ".plx" in logs_path:
            logs_data = V1Logs.read_csv(content)
            if to_structured:
                return logs_data.logs
            return logs_data.to_dict().get("logs", [])
        # Chunked logs
        data = orjson_loads(content)
        if to_structured:
            return V1Logs.from_dict(data).logs
        return data.get("logs", [])

    return await convert()


async def download_agent_logs_file(
    fs: FSSystem,
    store_path: str,
    agent_uuid: str,
    service: str,
    last_file: str,
    check_cache: bool = True,
) -> (str, str):
    subpath = ".agents/{}/logs/{}/{}".format(agent_uuid, service, last_file)
    content = await open_file(
        fs=fs, store_path=store_path, subpath=subpath, check_cache=check_cache
    )

    return await content_to_logs(content, subpath)


async def download_run_logs_file(
    fs: FSSystem,
    store_path: str,
    run_uuid: str,
    last_file: str,
    check_cache: bool = True,
) -> (str, str):
    subpath = "{}/plxlogs/{}".format(run_uuid, last_file)
    content = await open_file(
        fs=fs, store_path=store_path, subpath=subpath, check_cache=check_cache
    )

    return await content_to_logs(content, subpath)


async def download_tmp_logs(fs: FSSystem, store_path: str, run_uuid: str) -> str:
    subpath = "{}/.tmpplxlogs".format(run_uuid)
    delete_path(subpath)
    return await download_dir(fs=fs, store_path=store_path, subpath=subpath)
