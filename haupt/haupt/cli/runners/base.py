import logging
import os

from typing import List, Optional

from clipped.utils.lists import to_list
from clipped.utils.workers import get_core_workers

import uvicorn

from polyaxon.env_vars.keys import EV_KEYS_PROXY_LOCAL_PORT

_logger = logging.getLogger("haupt.cli")


def manage(command: str, args: Optional[List[str]] = None):
    from django.core.management import execute_from_command_line

    # Required env var to trigger a management command
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "haupt.polyconf.settings")

    argv = ["manage.py"]
    if command:
        argv.append(command)
    argv += to_list(args, check_none=True)
    execute_from_command_line(argv)


def migrate(
    migrate_tables: bool = False,
    migrate_db: bool = False,
):
    # Required env var to trigger a management command
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "haupt.polyconf.settings")

    if migrate_tables:
        _logger.info("Starting tables migration ...")
        manage("tables")
        _logger.info("Tables were migrated correctly!")

    if migrate_db:
        manage("migrate")
        _logger.info("DB Migration finished!")


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
):
    migrate(migrate_tables=migrate_tables, migrate_db=migrate_db)
    host = host or "0.0.0.0"
    port = int(port or 8000)
    os.environ[EV_KEYS_PROXY_LOCAL_PORT] = str(port)
    log_level = log_level or "warning"
    if per_core:
        workers = get_core_workers(per_core=workers or 2, max_workers=max_workers)
    else:
        workers = workers or get_core_workers(per_core=2, max_workers=max_workers)

    _logger.info(
        "{app_name} is running on http://{host}:{port} in process {pid} with {workers} workers".format(
            app_name=app_name, host=host, port=port, pid=os.getpid(), workers=workers
        )
    )
    uvicorn.run(
        app,
        host=host,
        port=port,
        access_log=False,
        log_level=log_level.lower(),
        workers=workers,
        uds=uds,
        timeout_keep_alive=120,
    )
