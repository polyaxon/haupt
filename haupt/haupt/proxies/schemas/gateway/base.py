from haupt import settings
from haupt.proxies.schemas.auth import get_auth_config
from haupt.proxies.schemas.base import clean_config
from haupt.proxies.schemas.dns import get_resolver
from haupt.proxies.schemas.gateway.api import get_api_location_config
from haupt.proxies.schemas.gateway.healthz import get_healthz_location_config
from haupt.proxies.schemas.locations import get_platform_locations_config
from haupt.proxies.schemas.scaffold import get_scaffold_config
from haupt.proxies.schemas.streams.api import get_platform_config
from haupt.proxies.schemas.streams.k8s import get_k8s_root_location_config


def get_base_config(is_platform: bool = True):
    resolver = get_resolver()
    auth = get_auth_config()
    if is_platform:
        api_configs = [
            get_platform_config(),
        ]
        api_location_configs = [
            get_platform_locations_config(),
            get_k8s_root_location_config(),
        ]
        port = settings.PROXIES_CONFIG.api_target_port
    else:
        api_configs = None
        api_location_configs = [
            get_api_location_config(resolver=resolver, auth=auth),
            get_healthz_location_config(),
        ]
        port = settings.PROXIES_CONFIG.gateway_target_port
    config = get_scaffold_config(
        is_proxy=not is_platform,
        port=port,
        use_ssl_config=True,
        use_assets_config=True,
        use_services_configs=True,
        resolver=resolver,
        auth=auth,
        api_configs=api_configs,
        api_location_configs=api_location_configs,
        is_local_streams_service=is_platform,
    )

    return clean_config(config)
