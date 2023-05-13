import os

from typing import Optional

from haupt.cli.runners.base import start_app
from polyaxon.services.values import PolyaxonServices


def start(
    host: Optional[str] = None,
    port: Optional[int] = None,
    log_level: Optional[str] = None,
    workers: Optional[int] = None,
    per_core: bool = False,
    uds: Optional[str] = None,
):
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
