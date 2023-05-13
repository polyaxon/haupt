from typing import Optional

from haupt.proxies.generators.base import write_to_conf_file
from haupt.proxies.schemas.forward import get_forward_cmd


def generate_forward_proxy_cmd(path: Optional[str] = None):
    cmd = get_forward_cmd()
    if cmd:
        write_to_conf_file("forward_proxy", cmd, path, "sh")
