#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.proxies.schemas.base import get_config

OPTIONS = """
gzip                        on;
gzip_disable                "msie6";
gzip_types                  *;
gzip_proxied                any;
"""


def get_gzip_config():
    return get_config(options=OPTIONS, indent=0)
