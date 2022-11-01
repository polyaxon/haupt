#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from haupt.cli.runners.base import start_app
from polyaxon.services.values import PolyaxonServices


def start(
    host: str = None,
    port: int = None,
    log_level: str = None,
    workers: int = None,
    per_core: bool = False,
    uds: str = None,
):
    start_app(
        app="haupt.polyconf.asgi:application",
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
