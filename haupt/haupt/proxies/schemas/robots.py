#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.proxies.schemas.base import get_config

OPTIONS = """
location = /robots.txt {{
    rewrite ^ /static/robots.txt;
}}
"""


def get_robots_config():
    return get_config(options=OPTIONS, indent=0)
