#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import os

from haupt import settings
from haupt.cli.runners.base import start_app
from polyaxon import settings as plx_settings
from polyaxon.env_vars.keys import (
    EV_KEYS_SANDBOX_ROOT,
    EV_KEYS_SERVICE,
    EV_KEYS_UI_IN_SANDBOX,
)
from polyaxon.services.values import PolyaxonServices


def start(
    host: str = None,
    port: int = None,
    log_level: str = None,
    workers: int = None,
    per_core: bool = False,
    uds: str = None,
    path: str = None,
):
    settings.set_sandbox_config()

    if path:
        os.environ[EV_KEYS_SANDBOX_ROOT] = path
    os.environ[EV_KEYS_UI_IN_SANDBOX] = "true"
    os.environ[EV_KEYS_SERVICE] = PolyaxonServices.API
    host = host or settings.SANDBOX_CONFIG.host
    port = port or settings.SANDBOX_CONFIG.port

    start_app(
        app="haupt.polyconf.asgi:application",
        app_name=PolyaxonServices.SANDBOX,
        host=host,
        port=port,
        log_level=log_level or plx_settings.CLIENT_CONFIG.log_level,
        workers=workers or settings.SANDBOX_CONFIG.workers,
        per_core=per_core or settings.SANDBOX_CONFIG.per_core,
        uds=uds,
        migrate_tables=True,
        migrate_db=True,
    )
