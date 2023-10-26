import os

from typing import Optional

from haupt import settings
from haupt.cli.runners.base import start_app
from polyaxon import settings as plx_settings
from polyaxon._env_vars.keys import ENV_KEYS_SERVICE
from polyaxon._services.values import PolyaxonServices


def start(
    host: Optional[str] = None,
    port: Optional[int] = None,
    log_level: Optional[str] = None,
    workers: Optional[int] = None,
    per_core: bool = False,
    uds: Optional[str] = None,
):
    os.environ[ENV_KEYS_SERVICE] = PolyaxonServices.API
    settings.set_sandbox_config(persist=True)
    host = host or settings.SANDBOX_CONFIG.host
    port = port or settings.SANDBOX_CONFIG.port
    start_app(
        app="haupt.polyconf.asgi.sandbox:application",
        app_name=PolyaxonServices.SANDBOX,
        host=host,
        port=port,
        log_level=log_level or plx_settings.CLIENT_CONFIG.log_level,
        workers=workers or settings.SANDBOX_CONFIG.workers,
        per_core=per_core or settings.SANDBOX_CONFIG.per_core,
        uds=uds,
        migrate_tables=True,
        migrate_db=True,
        use_cron=True,
    )
