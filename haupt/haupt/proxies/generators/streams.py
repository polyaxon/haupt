#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from typing import Optional

from haupt.proxies.generators.base import write_to_conf_file
from haupt.proxies.schemas.server import get_server_config
from haupt.proxies.schemas.streams import get_base_config


def generate_streams_conf(path: Optional[str] = None, root: Optional[str] = None):
    write_to_conf_file(
        "polyaxon.main",
        get_server_config(root=root, use_upstream=True, use_redirect=False),
        path,
    )
    write_to_conf_file("polyaxon.base", get_base_config(), path)
