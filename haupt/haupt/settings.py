from clipped.formatting import Printer
from pydantic import ValidationError

from polyaxon.services.values import PolyaxonServices

PROXIES_CONFIG = None
SANDBOX_CONFIG = None

PolyaxonServices.set_service_name()


def set_proxies_config():
    from haupt.managers.proxies import ProxiesManager

    global PROXIES_CONFIG

    PROXIES_CONFIG = ProxiesManager.get_config_from_env()


def set_sandbox_config():
    from haupt.managers.sandbox import SandboxConfigManager
    from polyaxon.contexts.paths import mount_sandbox
    from polyaxon.settings import HOME_CONFIG, set_agent_config

    SandboxConfigManager.set_config_path(HOME_CONFIG.path)
    mount_sandbox()
    PolyaxonServices.set_service_name(PolyaxonServices.SANDBOX)

    global SANDBOX_CONFIG

    try:
        SANDBOX_CONFIG = SandboxConfigManager.get_config_or_default()
        set_agent_config(SANDBOX_CONFIG)
    except (TypeError, ValidationError):
        SandboxConfigManager.purge()
        Printer.warning("Your sandbox configuration was purged!")
