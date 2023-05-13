from haupt.proxies.schemas.base import get_config

HEALTHZ_LOCATION_OPTIONS = r"""
location /healthz/ {{
    access_log off;
    return 200 "healthy";
}}
"""


def get_healthz_location_config():
    return get_config(
        options=HEALTHZ_LOCATION_OPTIONS,
        indent=0,
    )
