from typing import Optional

from haupt import settings
from haupt.proxies.schemas.base import clean_config, get_config
from haupt.proxies.schemas.urls import (
    get_header_host,
    get_service_proxy,
    get_service_url,
    get_ssl_server_name,
)
from polyaxon.api import (
    ADMIN_V1_LOCATION,
    API_V1_LOCATION,
    AUTH_V1_LOCATION,
    SSO_V1_LOCATION,
    UI_V1_LOCATION,
)

OPTIONS = r"""
location {path} {{
    {cors}
    {auth}
    {resolver}
    {ssl_server_name}
    proxy_pass {service};
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    {header_host}
    proxy_buffering off;
}}
"""  # noqa


def get_api_config(
    path: str,
    service: str,
    resolver: str,
    cors: str,
    auth: str,
    ssl_server_name: str,
    header_host: str,
):
    return get_config(
        options=OPTIONS,
        path=path,
        service=service,
        resolver=resolver,
        cors=cors,
        auth=auth,
        ssl_server_name=ssl_server_name,
        header_host=header_host,
    )


def get_api_location_config(
    resolver: str, cors: Optional[str] = "", auth: Optional[str] = ""
):
    service = get_service_url(
        host=settings.PROXIES_CONFIG.api_host,
        port=settings.PROXIES_CONFIG.api_port,
    )
    if not settings.PROXIES_CONFIG.api_use_resolver:
        resolver = ""
    if not settings.PROXIES_CONFIG.ui_single_url:
        cors = ""
    if not settings.PROXIES_CONFIG.auth_external:
        auth = ""
    ssl_server_name = get_ssl_server_name(service)
    header_host = get_header_host(service)
    if settings.PROXIES_CONFIG.has_forward_proxy:
        service = get_service_proxy(settings.PROXIES_CONFIG.forward_proxy_protocol)
    config = [
        get_api_config(
            path="= /",
            service=service,
            resolver=resolver,
            cors=cors,
            auth=auth,
            ssl_server_name=ssl_server_name,
            header_host=header_host,
        ),
        get_api_config(
            path=API_V1_LOCATION,
            service=service,
            resolver=resolver,
            cors=cors,
            auth=auth,
            ssl_server_name=ssl_server_name,
            header_host=header_host,
        ),
        get_api_config(
            path=AUTH_V1_LOCATION,
            service=service,
            resolver=resolver,
            cors=cors,
            auth="",
            ssl_server_name=ssl_server_name,
            header_host=header_host,
        ),
        get_api_config(
            path=UI_V1_LOCATION,
            service=service,
            resolver=resolver,
            cors=cors,
            auth="",
            ssl_server_name=ssl_server_name,
            header_host=header_host,
        ),
        get_api_config(
            path=SSO_V1_LOCATION,
            service=service,
            resolver=resolver,
            cors=cors,
            auth="",
            ssl_server_name=ssl_server_name,
            header_host=header_host,
        ),
        get_api_config(
            path="/static/",
            service=service,
            resolver=resolver,
            cors=cors,
            auth="",
            ssl_server_name=ssl_server_name,
            header_host=header_host,
        ),
    ]
    if settings.PROXIES_CONFIG.ui_admin_enabled:
        config.append(
            get_api_config(
                path=ADMIN_V1_LOCATION,
                service=service,
                resolver=resolver,
                cors=cors,
                auth=auth,
                ssl_server_name=ssl_server_name,
                header_host=header_host,
            )
        )
    return clean_config(config)
