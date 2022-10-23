#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.proxies.generators.base import write_to_conf_file
from haupt.proxies.schemas.gateway import get_base_config, get_redirect_config
from haupt.proxies.schemas.server import get_server_config


def generate_gateway_conf(path: str = None, root: str = None):
    write_to_conf_file(
        "polyaxon.main",
        get_server_config(root=root, use_upstream=False, use_redirect=True),
        path,
    )
    write_to_conf_file("polyaxon.base", get_base_config(), path)
    write_to_conf_file("polyaxon.redirect", get_redirect_config(), path)
