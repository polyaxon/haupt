import logging
import os

from typing import Optional

from clipped.utils.workers import get_core_workers

import uvicorn

from haupt.cli.runners.cron import start_cron
from haupt.cli.runners.manage import migrate
from polyaxon._env_vars.keys import ENV_KEYS_PROXY_LOCAL_PORT

_logger = logging.getLogger("haupt.cli")


def start_app(
    app,
    app_name,
    host: Optional[str] = None,
    port: Optional[int] = None,
    log_level: Optional[str] = None,
    workers: Optional[int] = None,
    per_core: bool = False,
    max_workers: Optional[int] = None,
    uds: Optional[str] = None,
    migrate_tables: bool = False,
    migrate_db: bool = False,
    use_cron: bool = False,
):
    migrate(migrate_tables=migrate_tables, migrate_db=migrate_db)
    host = host or "0.0.0.0"
    port = int(port or 8000)
    os.environ[ENV_KEYS_PROXY_LOCAL_PORT] = str(port)
    log_level = log_level or "warning"
    if per_core:
        workers = get_core_workers(per_core=workers or 2, max_workers=max_workers)
    else:
        workers = workers or get_core_workers(per_core=2, max_workers=max_workers)

    dashboard_url = os.environ.get("POLYAXON_DASHBOARD_URL", f"http://{host}:{port}")
    _logger.info(
        "{app_name} is running on {dashboard_url} in process {pid} with {workers} workers".format(
            app_name=app_name,
            dashboard_url=dashboard_url,
            pid=os.getpid(),
            workers=workers,
        )
    )
    if use_cron:
        start_cron(host=f"http://{host}:{port}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        access_log=False,
        log_level=log_level.lower(),
        workers=int(workers),
        uds=uds,
        timeout_keep_alive=120,
    )
