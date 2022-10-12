#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.proxies.generators.base import write_to_conf_file
from haupt.proxies.schemas.gateway import (
    get_base_config,
    get_forward_cmd,
    get_main_config,
    get_redirect_config,
)


def generate_gateway_conf(path=None, root=None):
    write_to_conf_file("polyaxon.main", get_main_config(root), path)
    write_to_conf_file("polyaxon.base", get_base_config(), path)
    write_to_conf_file("polyaxon.redirect", get_redirect_config(), path)


def generate_forward_proxy_cmd(path=None):
    cmd = get_forward_cmd()
    if cmd:
        write_to_conf_file("forward_proxy", cmd, path, "sh")
