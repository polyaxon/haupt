from haupt import settings
from haupt.proxies.schemas.base import get_config

OPTIONS = r"""
#!/bin/bash
set -e
set -o pipefail

{cmd}
"""


def get_forward_cmd():
    if not settings.PROXIES_CONFIG.has_forward_proxy:
        return

    cmd = None
    if settings.PROXIES_CONFIG.forward_proxy_kind == "transparent":
        cmd = "socat TCP4-LISTEN:8443,reuseaddr,fork TCP:{proxy_host}:{proxy_port}".format(
            proxy_host=settings.PROXIES_CONFIG.forward_proxy_host,
            proxy_port=settings.PROXIES_CONFIG.forward_proxy_port,
        )
    elif (
        settings.PROXIES_CONFIG.forward_proxy_kind is None
        or settings.PROXIES_CONFIG.forward_proxy_kind == "connect"
    ):
        cmd = (
            "socat TCP4-LISTEN:8443,reuseaddr,fork,bind=127.0.0.1 "
            "PROXY:{proxy_host}:{api_host}:{api_port},proxyport={proxy_port}".format(
                api_host=settings.PROXIES_CONFIG.api_host,
                api_port=settings.PROXIES_CONFIG.api_port,
                proxy_host=settings.PROXIES_CONFIG.forward_proxy_host,
                proxy_port=settings.PROXIES_CONFIG.forward_proxy_port,
            )
        )

    if not cmd:
        return

    return get_config(
        options=OPTIONS,
        indent=0,
        cmd=cmd,
    )
