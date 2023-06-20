from typing import Dict

from clipped.utils.json import orjson_dumps

from polyaxon.fs.async_manager import upload_data
from polyaxon.fs.types import FSSystem


async def upload_op_spec(fs: FSSystem, store_path: str, run_uuid: str, op_spec: Dict):
    subpath = "{}/outputs/spec.json".format(run_uuid)
    await upload_data(
        fs=fs, store_path=store_path, subpath=subpath, data=orjson_dumps(op_spec)
    )
