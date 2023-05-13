from haupt.managers.platform import PlatformManager
from polyaxon.settings import HOME_CONFIG

PlatformManager.set_config_path(HOME_CONFIG.path)
PLATFORM_CONFIG = PlatformManager.get_config_from_env(file_path=__file__)
