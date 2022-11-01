#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from haupt import settings
from haupt.cli.runners.base import start_app
from polyaxon import settings as plx_settings
from polyaxon.services.values import PolyaxonServices


def start(
    host: str = None,
    port: int = None,
    log_level: str = None,
    workers: int = None,
    per_core: bool = False,
    uds: str = None,
):
    settings.set_sandbox_config()

    start_app(
        app="haupt.polyconf.asgi:application",
        app_name=PolyaxonServices.SANDBOX,
        host=host or settings.SANDBOX_CONFIG.host,
        port=port or settings.SANDBOX_CONFIG.port,
        log_level=log_level or plx_settings.CLIENT_CONFIG.log_level,
        workers=workers or settings.SANDBOX_CONFIG.workers,
        per_core=per_core or settings.SANDBOX_CONFIG.per_core,
        uds=uds,
        migrate_tables=True,
        migrate_db=True,
    )
