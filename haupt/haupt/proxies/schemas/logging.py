from haupt import settings
from haupt.proxies.schemas.base import get_config

OPTIONS = """
error_log {root}/error.log {level};
"""


def get_logging_config():
    return get_config(
        options=OPTIONS,
        indent=0,
        root=settings.PROXIES_CONFIG.logs_root,
        level=settings.PROXIES_CONFIG.get_log_level(),
    )
