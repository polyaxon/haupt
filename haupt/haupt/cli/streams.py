#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import os


def start_streams(host: str, port: int, workers: int, per_core: bool, uds: str):
    """Start streams service."""
    from cli.runners.streams import start
    from polyaxon.env_vars.keys import EV_KEYS_PROXY_STREAMS_TARGET_PORT

    port = port or os.environ.get(EV_KEYS_PROXY_STREAMS_TARGET_PORT)
    start(host=host, port=port, workers=workers, per_core=per_core, uds=uds)
