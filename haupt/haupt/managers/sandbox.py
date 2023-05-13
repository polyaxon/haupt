import os

from haupt.schemas.sandbox_config import SandboxConfig
from polyaxon.config.manager import ConfigManager


class SandboxConfigManager(ConfigManager):
    """Manages sandbox configuration .sandbox file."""

    VISIBILITY = ConfigManager.Visibility.ALL
    CONFIG_FILE_NAME = ".sandbox"
    CONFIG = SandboxConfig

    @classmethod
    def get_config_from_env(cls):
        config_paths = [os.environ, {"dummy": "dummy"}]

        config = cls._CONFIG_READER.read_configs(config_paths)
        return cls.CONFIG.from_dict(config.data)

    @classmethod
    def get_config_or_default(cls) -> SandboxConfig:
        if not cls.is_initialized():
            return cls.get_config_from_env()

        return cls.get_config()
