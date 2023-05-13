from haupt import settings
from haupt.proxies.schemas.base import get_config

HTTP_OPTIONS = """
listen {port};
"""

SSL_OPTIONS = """
listen 443 ssl;
ssl on;
"""


def get_listen_config(is_proxy: bool, port: int = 8000) -> str:
    options = (
        SSL_OPTIONS
        if is_proxy and settings.PROXIES_CONFIG.ssl_enabled
        else HTTP_OPTIONS
    )
    return get_config(options=options, indent=0, port=port)
