import datetime
import os

from typing import List, Optional, Tuple

import aiofiles

from haupt.streams.tasks.logs import (
    content_to_logs,
    download_agent_logs_file,
    download_logs,
    download_run_logs_file,
)
from polyaxon._fs.async_manager import list_files
from polyaxon._fs.types import FSSystem
from polyaxon._k8s.logging.async_monitor import query_k8s_operation_logs
from polyaxon._k8s.manager.async_manager import AsyncK8sManager
from traceml.events import get_logs_path
from traceml.logging import V1Log


async def get_agent_logs_files(
    fs: FSSystem, store_path: str, agent_uuid: str, service: str
) -> List[str]:
    files = await list_files(
        fs=fs,
        store_path=store_path,
        subpath=".agents/{}/logs/{}".format(agent_uuid, service),
    )
    if not files["files"]:
        return []
    return sorted([f for f in files["files"].keys()])


async def get_run_logs_files(fs: FSSystem, store_path: str, run_uuid: str) -> List[str]:
    files = await list_files(
        fs=fs,
        store_path=store_path,
        subpath=get_logs_path(run_path=run_uuid, full_path=False),
    )
    if not files["files"]:
        return []
    return sorted([f for f in files["files"].keys()])


async def get_next_file(
    files: List[str], last_file: Optional[str] = None
) -> Optional[str]:
    if not files:
        return None

    if not last_file:
        return files[0]

    i = 0
    for i, f in enumerate(files):
        if f == last_file:
            break
    i += 1
    if i >= len(files):
        return None

    return files[i]


async def read_logs_file(logs_path) -> List[V1Log]:
    if not logs_path or not os.path.exists(logs_path):
        return []

    async with aiofiles.open(logs_path, mode="r") as f:
        content = await f.read()
        return await content_to_logs(content, logs_path, to_structured=True)


async def get_archived_agent_logs(
    fs: FSSystem,
    store_path: str,
    agent_uuid: str,
    service: str,
    last_file: Optional[str],
    check_cache: bool = True,
) -> Tuple[List[V1Log], Optional[str], List[str]]:
    files = await get_agent_logs_files(
        fs=fs, store_path=store_path, agent_uuid=agent_uuid, service=service
    )
    logs = []
    last_file = await get_next_file(files=files, last_file=last_file)
    if not last_file:
        return logs, last_file, files

    logs = await download_agent_logs_file(
        fs=fs,
        store_path=store_path,
        agent_uuid=agent_uuid,
        service=service,
        last_file=last_file,
        check_cache=check_cache,
    )

    return logs, last_file, files


async def get_legacy_archived_operation_logs(
    fs: FSSystem,
    store_path: str,
    run_uuid: str,
    last_file: Optional[str],
    check_cache: bool = True,
) -> Tuple[List[V1Log], Optional[str], List[str]]:
    files = await get_run_logs_files(fs=fs, store_path=store_path, run_uuid=run_uuid)
    logs = []
    last_file = await get_next_file(files=files, last_file=last_file)
    if not last_file:
        return logs, last_file, files

    logs = await download_run_logs_file(
        fs=fs,
        store_path=store_path,
        run_uuid=run_uuid,
        last_file=last_file,
        check_cache=check_cache,
    )

    return logs, last_file, files


async def get_archived_pods_operation_logs(
    fs: FSSystem,
    store_path: str,
    run_uuid: str,
    subpath: str,
    last_time: Optional[datetime.datetime] = None,
    check_cache: bool = True,
) -> Tuple[List[V1Log], Optional[datetime.datetime]]:
    logs = []

    logs_path = await download_logs(
        fs=fs,
        store_path=store_path,
        subpath=subpath,
        run_uuid=run_uuid,
        check_cache=check_cache,
    )

    if not logs_path or not os.path.exists(logs_path):
        return logs, None

    log_files = os.listdir(logs_path)
    if not log_files:
        return logs, None

    for log_file in log_files:
        _logs_path = os.path.join(logs_path, log_file)
        logs += await read_logs_file(_logs_path)

    if last_time:
        logs = [l for l in logs if l.timestamp > last_time]
    if logs:
        logs = sorted(logs, key=lambda x: x.timestamp)
        last_time = logs[-1].timestamp
    return [l.to_dict() for l in logs], last_time


async def get_tmp_operation_logs(
    fs: FSSystem, store_path: str, run_uuid: str, last_time: Optional[datetime.datetime]
) -> Tuple[List[V1Log], Optional[datetime.datetime]]:
    logs, last_time = await get_archived_pods_operation_logs(
        fs=fs,
        store_path=store_path,
        run_uuid=run_uuid,
        subpath="plxlogs",
        last_time=last_time,
        check_cache=False,
    )
    if logs:
        return logs, last_time
    return await get_archived_pods_operation_logs(
        fs=fs,
        store_path=store_path,
        run_uuid=run_uuid,
        subpath=".tmpplxlogs",
        last_time=last_time,
    )


async def get_archived_operation_logs(
    fs: FSSystem,
    store_path: str,
    run_uuid: str,
    last_file: Optional[str],
    check_cache: bool = True,
) -> Tuple[List[V1Log], Optional[str], List[str]]:
    logs, _ = await get_archived_pods_operation_logs(
        fs=fs,
        store_path=store_path,
        run_uuid=run_uuid,
        subpath="plxlogs",
        check_cache=check_cache,
    )
    if logs:
        return logs, None, []
    return await get_legacy_archived_operation_logs(
        fs=fs,
        store_path=store_path,
        run_uuid=run_uuid,
        last_file=last_file,
        check_cache=check_cache,
    )


async def get_k8s_operation_logs(
    k8s_manager: AsyncK8sManager,
    k8s_operation: any,
    instance: str,
    last_time: Optional[datetime.datetime],
):
    operation_logs, last_time = await query_k8s_operation_logs(
        instance=instance,
        last_time=last_time,
        k8s_manager=k8s_manager,
        stream=True,
    )
    if k8s_operation.get("status", {}).get("completionTime"):
        last_time = None
    if operation_logs:
        operation_logs = [l.to_dict() for l in operation_logs]

    return operation_logs, last_time
