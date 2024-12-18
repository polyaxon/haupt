from haupt import settings
from haupt.proxies.schemas.base import get_config

CORS_OPTIONS = r"""
    if ($request_method = 'OPTIONS') {{
        add_header 'Access-Control-Allow-Origin' "$http_origin" always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Access-Control-Allow-Headers' 'X-POLYAXON-SERVICE,x-csrftoken,X-CSRF-Token,Authorization,Accept,Origin,DNT,X-Mx-ReqToken,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range,Sec-Fetch-Mode,User-Agent' always;
        add_header 'Access-Control-Allow-Methods' 'GET,POST,OPTIONS,PUT,DELETE,PATCH' always;
        add_header 'Access-Control-Max-Age' 1728000 always;
        add_header 'Content-Length' 0;
        add_header 'Content-Type' 'text/plain; charset=utf-8';
        return 204;
    }}

    add_header 'Access-Control-Allow-Origin' "$http_origin" always;
    add_header 'Access-Control-Allow-Credentials' 'true' always;
    add_header 'Access-Control-Allow-Methods' 'GET,POST,OPTIONS,PUT,DELETE,PATCH' always;
    add_header 'Access-Control-Allow-Headers' 'X-POLYAXON-SERVICE,x-csrftoken,X-CSRF-Token,Authorization,Accept,Origin,DNT,X-Mx-ReqToken,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range,Sec-Fetch-Mode,User-Agent' always;
"""  # noqa


def get_cors_config():
    return get_config(
        options=CORS_OPTIONS if settings.PROXIES_CONFIG.ui_single_url else "",
        indent=0,
    )
