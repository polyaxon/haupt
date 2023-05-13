from haupt import settings
from haupt.proxies.schemas.base import clean_config, get_config
from polyaxon.api import (
    ADMIN_V1_LOCATION,
    API_V1_LOCATION,
    AUTH_V1_LOCATION,
    HEALTHZ_LOCATION,
    SSO_V1_LOCATION,
    UI_V1_LOCATION,
)

API_OPTIONS = """
location {path} {{
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors {intercept_errors};
}}
"""


def get_api_config(path: str, intercept_errors: str = "on"):
    return get_config(
        options=API_OPTIONS, indent=0, path=path, intercept_errors=intercept_errors
    )


def get_platform_config():
    config = [
        get_api_config(path="= /"),
        get_api_config(path="= {}".format(HEALTHZ_LOCATION), intercept_errors="off"),
        get_api_config(path=API_V1_LOCATION, intercept_errors="off"),
        get_api_config(path=AUTH_V1_LOCATION, intercept_errors="off"),
        get_api_config(path=SSO_V1_LOCATION, intercept_errors="off"),
        get_api_config(path=UI_V1_LOCATION),
    ]
    if settings.PROXIES_CONFIG.ui_admin_enabled:
        config.append(get_api_config(path=ADMIN_V1_LOCATION))
    return clean_config(config)
