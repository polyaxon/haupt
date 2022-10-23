#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt import settings
from haupt.proxies.schemas.auth import get_auth_config
from haupt.proxies.schemas.base import clean_config
from haupt.proxies.schemas.dns import get_resolver
from haupt.proxies.schemas.gateway.api import get_api_location_config
from haupt.proxies.schemas.locations import get_streams_locations_config
from haupt.proxies.schemas.scaffold import get_scaffold_config
from haupt.proxies.schemas.streams.api import get_k8s_auth_config, get_streams_config
from haupt.proxies.schemas.streams.k8s import get_k8s_root_location_config


def get_base_config(is_gateway: bool = True):
    resolver = get_resolver()
    auth = get_auth_config()
    api_configs = [
        get_streams_config(),
        get_k8s_auth_config(),
    ]
    api_location_configs = [
        get_streams_locations_config(),
        get_k8s_root_location_config(),
    ]
    if is_gateway:
        api_location_configs.append(
            get_api_location_config(resolver=resolver, auth=auth)
        )
    config = get_scaffold_config(
        is_proxy=False,
        port=settings.PROXIES_CONFIG.streams_target_port,
        use_ssl_config=is_gateway,
        use_assets_config=is_gateway,
        use_services_configs=is_gateway,
        resolver=resolver,
        auth=auth,
        api_configs=api_configs,
        api_location_configs=api_location_configs,
        is_local_streams_service=is_gateway,
    )
    return clean_config(config)
