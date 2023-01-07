#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.proxies.schemas.base import get_config

HEALTHZ_LOCATION_OPTIONS = r"""
location /healthz/ {{
    access_log off;
    return 200 "healthy";
}}
"""


def get_healthz_location_config():
    return get_config(
        options=HEALTHZ_LOCATION_OPTIONS,
        indent=0,
    )
