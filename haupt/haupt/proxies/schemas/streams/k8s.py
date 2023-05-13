from haupt.proxies.schemas.base import get_config
from polyaxon.api import AUTH_REQUEST_V1_LOCATION, K8S_V1_LOCATION

K8S_LOCATION_OPTIONS = r"""
location {app} {{
    auth_request     {auth_request};
    auth_request_set $auth_status $upstream_status;
    auth_request_set $k8s_token $upstream_http_k8s_token;
    auth_request_set $k8s_uri $upstream_http_k8s_uri;
    proxy_pass $k8s_uri;
    proxy_http_version 1.1;
    proxy_redirect     off;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Authorization "bearer $k8s_token";
    proxy_buffering off;
}}
"""  # noqa


def get_k8s_root_location_config():
    return get_config(
        options=K8S_LOCATION_OPTIONS,
        app=K8S_V1_LOCATION,
        auth_request=AUTH_REQUEST_V1_LOCATION,
    )
