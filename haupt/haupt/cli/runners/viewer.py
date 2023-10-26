import os

from typing import Optional

from haupt import settings
from haupt.cli.runners.base import start_app
from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.keys import (
    ENV_KEYS_PROXY_STREAMS_TARGET_PORT,
    ENV_KEYS_SANDBOX_ROOT,
)
from polyaxon._services.values import PolyaxonServices


def start(
    host: Optional[str] = None,
    port: Optional[int] = None,
    log_level: Optional[str] = None,
    workers: Optional[int] = None,
    per_core: bool = False,
    uds: Optional[str] = None,
    path: Optional[str] = None,
):
    port = port or os.environ.get(ENV_KEYS_PROXY_STREAMS_TARGET_PORT)
    path = path or ctx_paths.CONTEXT_ARTIFACTS_ROOT
    settings.set_sandbox_config(path=path)
    os.environ[ENV_KEYS_SANDBOX_ROOT] = path
    start_app(
        app="haupt.polyconf.asgi.viewer:application",
        app_name=PolyaxonServices.STREAMS,
        host=host,
        port=port,
        log_level=log_level,
        workers=workers,
        per_core=per_core,
        uds=uds,
    )
