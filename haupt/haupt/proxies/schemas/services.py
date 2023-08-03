from haupt import settings
from haupt.proxies.schemas.base import get_config
from haupt.proxies.schemas.urls import get_service_url
from polyaxon.api import (
    AUTH_REQUEST_V1_LOCATION,
    EXTERNAL_V1_LOCATION,
    MONITORS_V1_LOCATION,
    REWRITE_EXTERNAL_V1_LOCATION,
    REWRITE_MONITORS_V1_LOCATION,
    REWRITE_SERVICES_V1_LOCATION,
    SERVICES_V1_LOCATION,
)

PLUGIN_OPTIONS = r"""
location ~ /{plugin_name}/proxy/([-_.:\w]+)/(.*) {{
    {auth}
    {resolver}
    rewrite_log on;
    rewrite ^/{plugin_name}/proxy/([-_.:\w]+)/(.*) /{plugin_name}/proxy/$1/$2 break;
    proxy_pass http://$1:{port};
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}}
"""  # noqa


def get_plugin_location_config(name: str, port: int, resolver: str, auth: str):
    return get_config(
        options=PLUGIN_OPTIONS,
        indent=0,
        plugin_name=name,
        port=port,
        resolver=resolver,
        auth=auth,
    )


def get_plugins_location_config(resolver: str, auth: str, proxy_services=None):
    plugins = []

    if proxy_services:
        for plugin, config in proxy_services.items():
            plugins.append(
                get_plugin_location_config(
                    name=plugin, port=config["port"], resolver=resolver, auth=auth
                )
            )

    return plugins


SERVICES_OPTIONS = r"""
location ~ {app}([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {{
    {auth}
    {resolver}
    proxy_pass http://plx-operation-$4.$1.svc.{dns_custom_cluster}:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}}
"""  # noqa

SERVICES_REWRITE_OPTIONS = r"""
location ~ {app}([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {{
    {auth}
    {resolver}
    rewrite_log on;
    rewrite ^{app}([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4.$1.svc.{dns_custom_cluster}:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}}
"""  # noqa

EXTERNAL_OPTIONS = r"""
location ~ {app}([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {{
    {resolver}
    proxy_pass http://plx-operation-$4-ext.$1.svc.{dns_custom_cluster}:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}}
"""  # noqa

EXTERNAL_REWRITE_OPTIONS = r"""
location ~ {app}([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {{
    {resolver}
    rewrite_log on;
    rewrite ^{app}([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4-ext.$1.svc.{dns_custom_cluster}:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}}
"""  # noqa


def get_services_location_config(
    resolver: str,
    auth: str,
    rewrite: bool = False,
    external: bool = False,
):
    if external:
        options = EXTERNAL_REWRITE_OPTIONS if rewrite else EXTERNAL_OPTIONS
        app = REWRITE_EXTERNAL_V1_LOCATION if rewrite else EXTERNAL_V1_LOCATION
    else:
        options = SERVICES_REWRITE_OPTIONS if rewrite else SERVICES_OPTIONS
        app = REWRITE_SERVICES_V1_LOCATION if rewrite else SERVICES_V1_LOCATION
    return get_config(
        options=options,
        app=app,
        resolver=resolver,
        auth="" if external else auth,
        dns_custom_cluster=settings.PROXIES_CONFIG.dns_custom_cluster,
    )


SERVICES_MONITORS_OPTIONS = r"""
location ~ {app}([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) {{
    {auth}
    {resolver}
    proxy_pass http://$5.$1.svc.{dns_custom_cluster}:$6;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}}
"""  # noqa

SERVICES_MONITORS_REWRITE_OPTIONS = r"""
location ~ {app}([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) {{
    {auth}
    {resolver}
    rewrite_log on;
    rewrite ^{app}([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) /$7 break;
    proxy_pass http://$5.$1.svc.{dns_custom_cluster}:$6;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}}
"""  # noqa


def get_service_monitors_location_config(
    resolver: str, auth: str, rewrite: bool = False
):
    options = (
        SERVICES_MONITORS_REWRITE_OPTIONS if rewrite else SERVICES_MONITORS_OPTIONS
    )
    app = REWRITE_MONITORS_V1_LOCATION if rewrite else MONITORS_V1_LOCATION
    return get_config(
        options=options,
        app=app,
        resolver=resolver,
        auth=auth,
        dns_custom_cluster=settings.PROXIES_CONFIG.dns_custom_cluster,
    )


def get_services_definitions(resolver: str, auth: str):
    return [
        get_services_location_config(
            resolver=resolver,
            auth=auth,
            rewrite=False,
            external=False,
        ),
        get_services_location_config(
            resolver=resolver,
            auth=auth,
            rewrite=True,
            external=False,
        ),
        get_services_location_config(
            resolver=resolver,
            auth=auth,
            rewrite=False,
            external=True,
        ),
        get_services_location_config(
            resolver=resolver,
            auth=auth,
            rewrite=True,
            external=True,
        ),
        get_service_monitors_location_config(
            resolver=resolver,
            auth=auth,
            rewrite=False,
        ),
        get_service_monitors_location_config(
            resolver=resolver,
            auth=auth,
            rewrite=True,
        ),
    ]


STREAMS_OPTIONS = r"""
location /streams/ {{
    {auth}
    {resolver}
    proxy_pass {service};
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}}
"""  # noqa


def get_streams_service(is_local_service: bool = False) -> str:
    return (
        "http://polyaxon"
        if is_local_service
        else get_service_url(
            host=settings.PROXIES_CONFIG.streams_host,
            port=settings.PROXIES_CONFIG.streams_port,
        )
    )


def get_streams_location_config(
    resolver: str, auth: str, is_local_service: bool = False
):
    service = get_streams_service(is_local_service)
    # Do not use resolve local streams service
    resolver = "" if is_local_service else resolver
    return get_config(
        options=STREAMS_OPTIONS, resolver=resolver, auth=auth, service=service
    )


K8S_OPTIONS = r"""
location /k8s/ {{
    {auth}
    {resolver}
    proxy_pass {service};
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}}
"""  # noqa


def get_k8s_location_config(resolver: str, auth: str, is_local_service: bool = False):
    service = get_streams_service(is_local_service)
    # Do not use resolve local streams service
    resolver = "" if is_local_service else resolver
    return get_config(
        options=K8S_OPTIONS, resolver=resolver, auth=auth, service=service
    )


INTERNAL_OPTIONS = r"""
location /internal/ {{
    {resolver}
    proxy_pass {service};
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}}
"""  # noqa


def get_internal_location_config(resolver: str, is_local_service: bool = False):
    service = get_streams_service(is_local_service)
    # Do not use resolve local streams service
    resolver = "" if is_local_service else resolver
    return get_config(options=INTERNAL_OPTIONS, resolver=resolver, service=service)


AUTH_REQUEST_OPTIONS = """
location = {app} {{
    proxy_pass {service};
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
    proxy_set_header Host $http_host;
    proxy_intercept_errors {intercept_errors};
    internal;
}}
"""


def get_auth_request_config():
    return get_config(
        options=AUTH_REQUEST_OPTIONS,
        app=AUTH_REQUEST_V1_LOCATION,
        service=get_streams_service(True),
        indent=0,
        intercept_errors="off",
    )
