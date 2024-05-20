from haupt import settings
from haupt.proxies.schemas.base import get_config
from haupt.proxies.schemas.urls import (
    get_header_host,
    get_service_proxy,
    get_service_url,
    get_ssl_server_name,
)
from polyaxon.api import AUTH_REQUEST_V1_LOCATION, AUTH_V1_LOCATION

AUTH_OPTIONS = r"""
    auth_request     {auth_api};
    auth_request_set $auth_status $upstream_status;
"""  # noqa


def get_auth_config(auth_api: str = AUTH_REQUEST_V1_LOCATION):
    return get_config(
        options=AUTH_OPTIONS if settings.PROXIES_CONFIG.auth_enabled else "",
        indent=0,
        auth_api=auth_api,
    )


AUTH_LOCATION_CONFIG = r"""
location = {auth_api} {{
    {resolver}
    {ssl_server_name}
    proxy_pass {service};
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
    {header_host}
    internal;
}}
"""


def get_auth_location_config(resolver: str, is_local_service: bool = False):
    """Note that this is not used anymore and was deprecated in favor of the new auth-request"""
    if settings.PROXIES_CONFIG.auth_external:
        service = settings.PROXIES_CONFIG.auth_external
    elif is_local_service:
        service = "http://polyaxon"
    else:
        service = get_service_url(
            host=settings.PROXIES_CONFIG.api_host,
            port=settings.PROXIES_CONFIG.api_port,
        )
    if is_local_service or not settings.PROXIES_CONFIG.auth_use_resolver:
        resolver = ""
    header_host = get_header_host(service)
    if settings.PROXIES_CONFIG.has_forward_proxy:
        service = get_service_proxy(
            protocol=settings.PROXIES_CONFIG.forward_proxy_protocol
        )
    return get_config(
        options=AUTH_LOCATION_CONFIG if settings.PROXIES_CONFIG.auth_enabled else "",
        indent=0,
        service=service,
        auth_api=AUTH_V1_LOCATION,
        resolver=resolver,
        ssl_server_name=get_ssl_server_name(service),
        header_host=header_host,
    )
