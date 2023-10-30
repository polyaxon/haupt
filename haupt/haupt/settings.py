from typing import Optional

from clipped.compact.pydantic import ValidationError
from clipped.formatting import Printer

from haupt.schemas.sandbox_config import SandboxConfig
from polyaxon._services.values import PolyaxonServices

PROXIES_CONFIG = None
SANDBOX_CONFIG = None

PolyaxonServices.set_service_name()


def set_proxies_config():
    from haupt.managers.proxies import ProxiesManager

    global PROXIES_CONFIG

    PROXIES_CONFIG = ProxiesManager.get_config_from_env()


def set_sandbox_config(
    config: Optional[SandboxConfig] = None,
    path: Optional[str] = None,
    persist: bool = False,
    env_only_config: bool = True,
):
    from haupt.managers.sandbox import SandboxConfigManager
    from polyaxon.settings import HOME_CONFIG, set_agent_config

    SandboxConfigManager.set_config_path(HOME_CONFIG.path)
    PolyaxonServices.set_service_name(PolyaxonServices.SANDBOX)

    global SANDBOX_CONFIG

    try:
        SANDBOX_CONFIG = (
            config or SandboxConfigManager.get_config_from_env()
            if env_only_config
            else SandboxConfigManager.get_config_or_default()
        )
        SANDBOX_CONFIG.mount_sandbox(path=path or HOME_CONFIG.path)
        SANDBOX_CONFIG.set_default_artifacts_store()
        if persist:
            SandboxConfigManager.set_config(SANDBOX_CONFIG)
        set_agent_config(SANDBOX_CONFIG)

    except (TypeError, ValidationError):
        SandboxConfigManager.purge()
        Printer.warning("Your sandbox configuration was purged!")
