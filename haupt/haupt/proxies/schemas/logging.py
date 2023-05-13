from haupt import settings
from haupt.proxies.schemas.base import get_config

OPTIONS = """
error_log {root}/error.log {level};
"""


def get_logging_config():
    log_level = settings.PROXIES_CONFIG.log_level
    if log_level and log_level.lower() == "warning":
        log_level = "warn"
    return get_config(
        options=OPTIONS,
        indent=0,
        root=settings.PROXIES_CONFIG.logs_root,
        level=log_level,
    )
