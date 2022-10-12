#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt import settings
from haupt.proxies.schemas.base import clean_config
from haupt.proxies.schemas.buffering import get_buffering_config
from haupt.proxies.schemas.charset import get_charset_config
from haupt.proxies.schemas.error_page import get_error_page_config
from haupt.proxies.schemas.gzip import get_gzip_config
from haupt.proxies.schemas.listen import get_listen_config
from haupt.proxies.schemas.locations import get_streams_locations_config
from haupt.proxies.schemas.logging import get_logging_config
from haupt.proxies.schemas.streams.api import get_api_config, get_k8s_auth_config
from haupt.proxies.schemas.streams.k8s import get_k8s_root_location_config
from haupt.proxies.schemas.timeout import get_timeout_config


def get_base_config():
    config = [
        get_listen_config(
            is_proxy=False, port=settings.PROXIES_CONFIG.streams_target_port
        )
    ]
    config += [
        get_logging_config(),
        get_gzip_config(),
        get_charset_config(),
        get_buffering_config(),
        get_timeout_config(),
        get_api_config(),
        get_k8s_auth_config(),
        get_error_page_config(),
        get_streams_locations_config(),
        get_k8s_root_location_config(),
    ]
    return clean_config(config)
