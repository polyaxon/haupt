#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt import settings
from haupt.proxies.schemas.auth import get_auth_config, get_auth_location_config
from haupt.proxies.schemas.base import clean_config
from haupt.proxies.schemas.dns import get_resolver
from haupt.proxies.schemas.gateway.api import get_api_location_config
from haupt.proxies.schemas.gateway.healthz import get_healthz_location_config
from haupt.proxies.schemas.scaffold import get_scaffold_config


def get_base_config():
    resolver = get_resolver()
    auth = get_auth_config()
    config = get_scaffold_config(
        is_proxy=True,
        port=settings.PROXIES_CONFIG.gateway_target_port,
        use_ssl_config=True,
        use_assets_config=True,
        api_configs=None,
        use_services_configs=True,
        resolver=resolver,
        auth=auth,
        api_location_configs=[
            get_api_location_config(resolver=resolver, auth=auth),
            get_healthz_location_config(),
        ],
    )
    # config += get_plugins_location_config(resolver=resolver, auth=auth)

    return clean_config(config)
