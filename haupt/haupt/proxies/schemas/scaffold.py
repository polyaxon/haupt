#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from typing import List

from haupt import settings
from haupt.proxies.schemas.auth import get_auth_location_config
from haupt.proxies.schemas.buffering import get_buffering_config
from haupt.proxies.schemas.charset import get_charset_config
from haupt.proxies.schemas.error_page import get_error_page_config
from haupt.proxies.schemas.favicon import get_favicon_config
from haupt.proxies.schemas.gzip import get_gzip_config
from haupt.proxies.schemas.listen import get_listen_config
from haupt.proxies.schemas.logging import get_logging_config
from haupt.proxies.schemas.robots import get_robots_config
from haupt.proxies.schemas.services import (
    get_k8s_location_config,
    get_services_location_config,
    get_streams_location_config,
)
from haupt.proxies.schemas.ssl import get_ssl_config
from haupt.proxies.schemas.timeout import get_timeout_config


def get_scaffold_config(
    is_proxy: bool,
    port: int = 8000,
    use_ssl_config: bool = False,
    use_assets_config: bool = False,
    use_services_configs: bool = False,
    resolver: str = None,
    auth: str = None,
    api_configs: List[str] = None,
    api_location_configs: List[str] = None,
    is_local_streams_service: bool = False,
    is_local_auth_service: bool = False,
) -> List[str]:
    config = [get_listen_config(is_proxy=is_proxy, port=port)]
    if use_ssl_config and settings.PROXIES_CONFIG.ssl_enabled:
        config.append(get_ssl_config())
    config += [
        get_logging_config(),
        get_gzip_config(),
        get_charset_config(),
        get_buffering_config(),
        get_timeout_config(),
    ]
    if api_configs:
        config += api_configs
    config.append(get_error_page_config())
    if use_assets_config:
        config += [
            get_robots_config(),
            get_favicon_config(),
        ]
    if use_services_configs:
        config += [
            get_auth_location_config(
                resolver=resolver, is_local_service=is_local_auth_service
            ),
            get_streams_location_config(
                resolver=resolver, auth=auth, is_local_service=is_local_streams_service
            ),
            get_k8s_location_config(
                resolver=resolver, auth=auth, is_local_service=is_local_streams_service
            ),
            get_services_location_config(
                resolver=resolver, auth=auth, rewrite=False, external=False
            ),
            get_services_location_config(
                resolver=resolver, auth=auth, rewrite=True, external=False
            ),
            get_services_location_config(
                resolver=resolver, auth=auth, rewrite=False, external=True
            ),
            get_services_location_config(
                resolver=resolver, auth=auth, rewrite=True, external=True
            ),
            # get_plugins_location_config(resolver=resolver, auth=auth)
        ]
    if api_location_configs:
        config += api_location_configs
    return config
