from haupt import settings
from haupt.proxies.schemas.base import get_config

OPTIONS = """
send_timeout {timeout};
keepalive_timeout {timeout};
uwsgi_read_timeout {timeout};
uwsgi_send_timeout {timeout};
client_header_timeout {timeout};
proxy_read_timeout {timeout};
keepalive_requests 10000;
"""


def get_timeout_config():
    return get_config(
        options=OPTIONS, indent=0, timeout=settings.PROXIES_CONFIG.nginx_timeout
    )
