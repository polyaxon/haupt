#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.proxies.schemas.base import get_config

OPTIONS = """
upstream polyaxon {{
  server unix:{root}/web/polyaxon.sock;
}}

server {{
    include polyaxon/polyaxon.base.conf;
}}
"""


def get_main_config(root=None):
    root = root or "/polyaxon"
    return get_config(options=OPTIONS, indent=0, root=root)
