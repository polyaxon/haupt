from typing import Optional

from haupt.proxies.generators.base import write_to_conf_file
from haupt.proxies.schemas.gateway import get_base_config, get_redirect_config
from haupt.proxies.schemas.server import get_server_config


def generate_gateway_conf(
    path: Optional[str] = None, root: Optional[str] = None, is_platform: bool = True
):
    write_to_conf_file(
        "polyaxon.main",
        get_server_config(root=root, use_upstream=is_platform, use_redirect=True),
        path,
    )
    write_to_conf_file("polyaxon.base", get_base_config(is_platform=is_platform), path)
    write_to_conf_file("polyaxon.redirect", get_redirect_config(), path)
