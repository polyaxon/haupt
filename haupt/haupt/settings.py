from typing import Optional

from clipped.compact.pydantic import ValidationError
from clipped.formatting import Printer

from polyaxon._services.values import PolyaxonServices

PROXIES_CONFIG = None
SANDBOX_CONFIG = None

PolyaxonServices.set_service_name()


def set_proxies_config():
    from haupt.managers.proxies import ProxiesManager

    global PROXIES_CONFIG

    PROXIES_CONFIG = ProxiesManager.get_config_from_env()


def set_sandbox_config(path: Optional[str] = None):
    from haupt.managers.sandbox import SandboxConfigManager
    from polyaxon._contexts.paths import mount_sandbox
    from polyaxon.settings import HOME_CONFIG, set_agent_config

    SandboxConfigManager.set_config_path(HOME_CONFIG.path)
    mount_sandbox(path=path)
    PolyaxonServices.set_service_name(PolyaxonServices.SANDBOX)

    global SANDBOX_CONFIG

    try:
        SANDBOX_CONFIG = SandboxConfigManager.get_config_or_default()
        set_agent_config(SANDBOX_CONFIG)
    except (TypeError, ValidationError):
        SandboxConfigManager.purge()
        Printer.warning("Your sandbox configuration was purged!")
