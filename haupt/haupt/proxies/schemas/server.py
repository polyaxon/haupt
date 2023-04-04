#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from typing import Optional

from haupt.proxies.schemas.base import clean_config, get_config

UPSTREAM_OPTIONS = """
upstream polyaxon {{
  server unix:{root}/web/polyaxon.sock;
}}
"""

SERVER_OPTIONS = """
server {{
    include polyaxon/polyaxon.base.conf;
}}
"""

REDIRECT_OPTIONS = """
include polyaxon/polyaxon.redirect.conf;
"""


def get_server_config(
    root: Optional[str] = None, use_upstream: bool = False, use_redirect: bool = False
):
    config = []
    if use_upstream:
        root = root or "/polyaxon"
        config.append(get_config(options=UPSTREAM_OPTIONS, indent=0, root=root))

    config.append(get_config(options=SERVER_OPTIONS, indent=0, root=root))
    if use_redirect:
        config.append(get_config(options=REDIRECT_OPTIONS, indent=0))
    return clean_config(config)
