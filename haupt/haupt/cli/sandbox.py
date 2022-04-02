#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import os


def start_sandbox(
    host: str, port: int, workers: int, per_core: bool, path: str, uds: str
):
    """Start sandbox service."""
    from cli.runners.sandbox import start
    from polyaxon.env_vars.keys import EV_KEYS_SANDBOX_ROOT, EV_KEYS_SERVICE
    from polyaxon.services.values import PolyaxonServices

    os.environ[EV_KEYS_SERVICE] = PolyaxonServices.SANDBOX
    if path:
        os.environ[EV_KEYS_SANDBOX_ROOT] = path

    start(host=host, port=port, workers=workers, per_core=per_core, uds=uds)
