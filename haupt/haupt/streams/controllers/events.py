import logging
import os

from typing import Dict, List, Optional, Set

from clipped.utils.json import orjson_loads

import aiofiles

from asgiref.sync import sync_to_async
from polyaxon._fs.async_manager import (
    download_file,
    download_files,
    list_files,
    tar_files,
)
from polyaxon._fs.types import FSSystem
from traceml.artifacts import V1ArtifactKind
from traceml.events import V1Events, get_event_path, get_resource_path

logger = logging.getLogger("haupt.streams.events")


async def get_events_files(
    fs: FSSystem, store_path: str, run_uuid: str, event_kind: str
) -> List[str]:
    subpath = get_event_path(run_path=run_uuid, kind=event_kind)
    files = await list_files(fs=fs, store_path=store_path, subpath=subpath)
    if not files["files"]:
        return []
    return sorted([f for f in files["files"].keys()])


async def get_resources_files(
    fs: FSSystem, store_path: str, run_uuid: str
) -> List[str]:
    subpath = get_resource_path(run_path=run_uuid, kind=V1ArtifactKind.METRIC)
    files = await list_files(fs=fs, store_path=store_path, subpath=subpath)
    if not files["files"]:
        return []
    return sorted([f for f in files["files"].keys()])


async def process_operation_event(
    event_path: str,
    event_kind: str,
    event_name: str,
    orient: str = V1Events.ORIENT_CSV,
    sample: Optional[int] = None,
    to_dict: bool = True,
) -> Optional[Dict]:
    if not event_path or not os.path.exists(event_path):
        return None

    async with aiofiles.open(event_path, mode="r") as f:
        contents = await f.read()
        if contents:
            if orient == V1Events.ORIENT_CSV:
                return {"name": event_name, "kind": event_kind, "data": contents}
            if orient == V1Events.ORIENT_DICT:
                event_df = await sync_to_async(V1Events.read)(
                    kind=event_kind,
                    name=event_name,
                    data=contents,
                    parse_dates=False,
                    engine="pyarrow",
                )
                if sample:
                    try:
                        sample = int(sample)
                        if event_df.df.shape[0] > sample:
                            event_df.df = event_df.df.sample(
                                n=sample, random_state=0
                            ).sort_index()
                    except Exception as e:
                        logger.warning("Could not sample event dataframe, error %s", e)
                return {
                    "name": event_name,
                    "kind": event_kind,
                    "data": event_df.to_dict() if to_dict else event_df,
                }
            else:
                logger.warning(
                    "received an unrecognisable orient value {}.".format(orient)
                )
    return None


async def get_archived_operation_resource(
    fs: FSSystem,
    store_path: str,
    run_uuid: str,
    event_kind: str,
    event_name: str,
    orient: str = V1Events.ORIENT_CSV,
    check_cache: bool = True,
    sample: Optional[int] = None,
) -> Optional[Dict]:
    subpath = get_resource_path(run_path=run_uuid, kind=event_kind, name=event_name)
    event_path = await download_file(
        fs=fs, store_path=store_path, subpath=subpath, check_cache=check_cache
    )

    return await process_operation_event(
        event_path=event_path,
        event_kind=event_kind,
        event_name=event_name,
        orient=orient,
        sample=sample,
    )


async def get_archived_operation_event(
    fs: FSSystem,
    store_path: str,
    run_uuid: str,
    event_kind: str,
    event_name: str,
    orient: str = V1Events.ORIENT_CSV,
    check_cache: bool = True,
    sample: Optional[int] = None,
) -> Optional[Dict]:
    subpath = get_event_path(run_path=run_uuid, kind=event_kind, name=event_name)
    event_path = await download_file(
        fs=fs, store_path=store_path, subpath=subpath, check_cache=check_cache
    )

    return await process_operation_event(
        event_path=event_path,
        event_kind=event_kind,
        event_name=event_name,
        orient=orient,
        sample=sample,
    )


async def get_archived_operation_event_and_assets(
    fs: FSSystem,
    store_path: str,
    run_uuid: str,
    event_kind: str,
    event_name: str,
    check_cache: bool = True,
) -> List[str]:
    pkg_files = []
    subpath = get_event_path(run_path=run_uuid, kind=event_kind, name=event_name)
    event_path = await download_file(
        fs=fs, store_path=store_path, subpath=subpath, check_cache=check_cache
    )
    pkg_files.append(event_path)

    event = await process_operation_event(
        event_path=event_path,
        event_kind=event_kind,
        event_name=event_name,
        orient=V1Events.ORIENT_DICT,
        sample=None,
        to_dict=False,
    )
    if not event:
        logger.warning("During the packaging of %s, the event download failed.")
        return []
    df = event["data"].df
    try:
        files = df[event_kind].map(lambda f: orjson_loads(f).get("path")).tolist()
    except Exception as e:
        logger.warning(
            "During the packaging of %s, the event format found was not correct. "
            "Error %s" % (event_path, e)
        )
        return pkg_files
    subpaths = []
    for file_from_path in files:
        subpaths.append("{}/{}".format(run_uuid, file_from_path))

    return await download_files(
        fs=fs,
        store_path=store_path,
        subpaths=subpaths,
        check_cache=check_cache,
        pkg_files=pkg_files,
    )


async def get_archived_operation_events_and_assets(
    fs: FSSystem,
    store_path: str,
    run_uuid: str,
    event_kind: str,
    event_names: Set[str],
    check_cache: bool = True,
) -> Optional[str]:
    pkg_files = []
    for event_name in event_names:
        event_pkg_files = await get_archived_operation_event_and_assets(
            fs=fs,
            store_path=store_path,
            run_uuid=run_uuid,
            event_kind=event_kind,
            event_name=event_name,
            check_cache=check_cache,
        )
        pkg_files += event_pkg_files
    return await tar_files(
        filename="{}.{}.{}".format(run_uuid, event_kind, "-and-".join(event_names)),
        pkg_files=pkg_files,
        subpath=run_uuid,
    )


async def get_archived_operation_resources(
    fs: FSSystem,
    store_path: str,
    run_uuid: str,
    event_kind: str,
    event_names: Set[str],
    orient: str = V1Events.ORIENT_CSV,
    check_cache: bool = True,
    sample: Optional[int] = None,
) -> List[Dict]:
    events = []
    if not event_names:
        files = await get_resources_files(
            fs=fs, store_path=store_path, run_uuid=run_uuid
        )
        event_names = [f.split(".plx")[0] for f in files]
    for event_name in event_names:
        event = await get_archived_operation_resource(
            fs=fs,
            store_path=store_path,
            run_uuid=run_uuid,
            event_kind=event_kind,
            event_name=event_name,
            orient=orient,
            check_cache=check_cache,
            sample=sample,
        )
        if event:
            events.append(event)
    return events


async def get_archived_operation_events(
    fs: FSSystem,
    store_path: str,
    run_uuid: str,
    event_kind: str,
    event_names: Set[str],
    orient: str = V1Events.ORIENT_CSV,
    check_cache: bool = True,
    sample: Optional[int] = None,
) -> List[Dict]:
    events = []
    for event_name in event_names:
        event = await get_archived_operation_event(
            fs=fs,
            store_path=store_path,
            run_uuid=run_uuid,
            event_kind=event_kind,
            event_name=event_name,
            orient=orient,
            check_cache=check_cache,
            sample=sample,
        )
        if event:
            events.append(event)
    return events


async def get_archived_operations_events(
    fs: FSSystem,
    store_path: str,
    event_kind: str,
    run_uuids: Set[str],
    event_names: Set[str],
    orient: str = V1Events.ORIENT_CSV,
    check_cache: bool = True,
    sample: Optional[int] = None,
) -> Dict[str, List]:
    events = {}
    for run_uuid in run_uuids:
        run_events = await get_archived_operation_events(
            fs=fs,
            store_path=store_path,
            run_uuid=run_uuid,
            event_kind=event_kind,
            event_names=event_names,
            orient=orient,
            check_cache=check_cache,
            sample=sample,
        )
        events[run_uuid] = run_events
    return events
