from haupt import settings
from haupt.proxies.schemas.api.uwsgi import get_uwsgi_config
from haupt.proxies.schemas.base import clean_config
from haupt.proxies.schemas.locations import get_api_locations_config
from haupt.proxies.schemas.scaffold import get_scaffold_config


def get_base_config():
    api_configs = [
        get_uwsgi_config(),
    ]
    api_location_configs = [get_api_locations_config()]
    config = get_scaffold_config(
        is_proxy=False,
        port=settings.PROXIES_CONFIG.api_target_port,
        use_ssl_config=False,
        use_assets_config=True,
        use_services_configs=False,
        api_configs=api_configs,
        api_location_configs=api_location_configs,
    )

    return clean_config(config)
