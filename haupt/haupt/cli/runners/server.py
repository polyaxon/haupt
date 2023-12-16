import os

from typing import Optional

from clipped.utils.bools import to_bool

from haupt.cli.runners.base import start_app
from polyaxon._env_vars.keys import (
    ENV_KEYS_PROXY_GATEWAY_CONCURRENCY,
    ENV_KEYS_PROXY_GATEWAY_PER_CORE,
)
from polyaxon._services.values import PolyaxonServices


def start(
    host: Optional[str] = None,
    port: Optional[int] = None,
    log_level: Optional[str] = None,
    workers: Optional[int] = None,
    per_core: bool = False,
    uds: Optional[str] = None,
):
    workers = workers or os.environ.get(ENV_KEYS_PROXY_GATEWAY_CONCURRENCY)
    per_core = per_core or to_bool(
        os.environ.get(ENV_KEYS_PROXY_GATEWAY_PER_CORE), handle_none=True
    )
    start_app(
        app="haupt.polyconf.asgi.server:application",
        app_name=PolyaxonServices.API,
        host=host,
        port=port,
        log_level=log_level,
        workers=workers,
        per_core=per_core,
        uds=uds,
        migrate_tables=True,
        migrate_db=True,
    )
