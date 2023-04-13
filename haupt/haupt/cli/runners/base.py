#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import logging
import os

from typing import Optional

from clipped.utils.workers import get_core_workers

import uvicorn

from polyaxon.env_vars.keys import EV_KEYS_PROXY_LOCAL_PORT

_logger = logging.getLogger("haupt.cli")


def migrate(
    migrate_tables: bool = False,
    migrate_db: bool = False,
):
    from django.core.management import execute_from_command_line

    # Required env var to trigger a management command
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "haupt.polyconf.settings")

    if migrate_tables:
        argv = ["manage.py", "tables"]
        _logger.info("Starting tables migration ...")
        execute_from_command_line(argv)
        _logger.info("Tables were migrated correctly!")

    if migrate_db:
        argv = ["manage.py", "migrate"]
        execute_from_command_line(argv)
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
            "{app_name} is running on http://{host}:{port} in process {pid}".format(
                app_name=app_name, host=host, port=port, pid=os.getpid()
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
