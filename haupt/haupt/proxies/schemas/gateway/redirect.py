#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt import settings
from haupt.proxies.schemas.base import get_config

SSL_REDIRECT_OPTIONS = r"""
server {{
    listen 80;
    return 301 https://$host$request_uri;
}}
"""


def get_redirect_config():
    return get_config(
        options=SSL_REDIRECT_OPTIONS if settings.PROXIES_CONFIG.ssl_enabled else "",
        indent=0,
        ssl_path=settings.PROXIES_CONFIG.ssl_path,
    )
