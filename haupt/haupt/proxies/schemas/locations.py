from haupt import settings
from haupt.proxies.schemas.base import get_config
from haupt.proxies.schemas.urls import get_ssl_server_name, has_https

STATIC_PROXY_OPTIONS = """
location /static/ {{
    {ssl_server_name}
    proxy_pass {service};
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
}}
"""


def get_static_proxy_config():
    return get_config(
        options=STATIC_PROXY_OPTIONS,
        indent=0,
        service=settings.PROXIES_CONFIG.static_url.rstrip("/") + "/",
        ssl_server_name=get_ssl_server_name(settings.PROXIES_CONFIG.static_url),
    )


STATIC_LOCATION_OPTIONS = """
location /static/ {{
    alias {static_root};
    autoindex on;
    expires                   30d;
    add_header                Cache-Control private;
    gzip_static on;
}}
"""


def get_static_location_config():
    return get_config(
        options=STATIC_LOCATION_OPTIONS,
        indent=0,
        static_root=settings.PROXIES_CONFIG.static_root.rstrip("/") + "/",
    )


TMP_LOCATION_OPTIONS = """
location /tmp/ {{
    alias                     /tmp/;
    expires                   0;
    add_header                Cache-Control private;
    internal;
}}
"""


def get_tmp_location_config():
    return get_config(options=TMP_LOCATION_OPTIONS, indent=0)


ARCHIVES_LOCATION_OPTIONS = """
location {archives_root} {{
    alias                     {archives_root};
    expires                   0;
    add_header                Cache-Control private;
    set                       $x_content_length $upstream_http_x_content_length;
    add_header                X-Content-Length $x_content_length;
    internal;
}}
"""


def get_archives_root_location_config():
    return get_config(
        options=ARCHIVES_LOCATION_OPTIONS,
        indent=0,
        archives_root=settings.PROXIES_CONFIG.archives_root.rstrip("/") + "/",
    )


def get_api_locations_config():
    if settings.PROXIES_CONFIG.static_url and has_https(
        settings.PROXIES_CONFIG.static_url
    ):
        static_location = get_static_proxy_config()
    else:
        static_location = get_static_location_config()
    config = [static_location, get_tmp_location_config()]
    return "\n".join(config)


def get_streams_locations_config():
    config = [
        get_tmp_location_config(),
        get_archives_root_location_config(),
    ]
    return "\n".join(config)


def get_platform_locations_config():
    if settings.PROXIES_CONFIG.static_url and has_https(
        settings.PROXIES_CONFIG.static_url
    ):
        static_location = get_static_proxy_config()
    else:
        static_location = get_static_location_config()
    config = [
        static_location,
        get_tmp_location_config(),
        get_archives_root_location_config(),
    ]
    return "\n".join(config)
