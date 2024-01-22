from typing import Dict

from clipped.utils.json import orjson_dumps

from polyaxon._fs.async_manager import download_file, upload_data
from polyaxon._fs.types import FSSystem


async def upload_op_spec(fs: FSSystem, store_path: str, run_uuid: str, op_spec: Dict):
    subpath = "{}/outputs/spec.json".format(run_uuid)
    await upload_data(
        fs=fs, store_path=store_path, subpath=subpath, data=orjson_dumps(op_spec)
    )


async def download_op_spec(fs: FSSystem, store_path: str, run_uuid: str):
    subpath = "{}/outputs/spec.json".format(run_uuid)
    return await download_file(
        fs=fs,
        store_path=store_path,
        subpath=subpath,
    )


async def upload_agent_spec(
    fs: FSSystem, store_path: str, agent_uuid: str, agent_spec: Dict
):
    subpath = ".agents/{}/outputs/spec.json".format(agent_uuid)
    await upload_data(
        fs=fs, store_path=store_path, subpath=subpath, data=orjson_dumps(agent_spec)
    )


async def download_agent_spec(fs: FSSystem, store_path: str, agent_uuid: str):
    subpath = ".agents/{}/outputs/spec.json".format(agent_uuid)
    return await download_file(
        fs=fs,
        store_path=store_path,
        subpath=subpath,
    )
