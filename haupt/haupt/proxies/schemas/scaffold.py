from typing import List, Optional

from haupt import settings
from haupt.proxies.schemas.buffering import get_buffering_config
from haupt.proxies.schemas.charset import get_charset_config
from haupt.proxies.schemas.error_page import get_error_page_config
from haupt.proxies.schemas.favicon import get_favicon_config
from haupt.proxies.schemas.gzip import get_gzip_config
from haupt.proxies.schemas.listen import get_listen_config
from haupt.proxies.schemas.logging import get_logging_config
from haupt.proxies.schemas.robots import get_robots_config
from haupt.proxies.schemas.services import (
    get_auth_request_config,
    get_internal_location_config,
    get_k8s_location_config,
    get_services_definitions,
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
    resolver: Optional[str] = None,
    auth: Optional[str] = None,
    api_configs: Optional[List[str]] = None,
    api_location_configs: Optional[List[str]] = None,
    is_local_streams_service: bool = False,
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
    if is_local_streams_service:
        config.append(
            get_auth_request_config(),
        )
    if use_services_configs:
        config += [
            get_internal_location_config(
                resolver=resolver, is_local_service=is_local_streams_service
            ),
            get_streams_location_config(
                resolver=resolver, auth=auth, is_local_service=is_local_streams_service
            ),
            get_k8s_location_config(
                resolver=resolver, auth=auth, is_local_service=is_local_streams_service
            ),
            # get_plugins_location_config(resolver=resolver, auth=auth)
        ]
        config += get_services_definitions(resolver=resolver, auth=auth)
    if api_location_configs:
        config += api_location_configs
    return config
