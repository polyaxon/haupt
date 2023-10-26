import os

from haupt.schemas.sandbox_config import SandboxConfig
from polyaxon._config.manager import ConfigManager


class SandboxConfigManager(ConfigManager):
    """Manages sandbox configuration .sandbox file."""

    VISIBILITY = ConfigManager.Visibility.ALL
    CONFIG_FILE_NAME = ".sandbox"
    CONFIG = SandboxConfig
    PERSIST_FORMAT = "yaml"

    @classmethod
    def get_config_from_env(cls):
        config_paths = [os.environ, {"dummy": "dummy"}]

        config = cls._CONFIG_READER.read_configs(config_paths)
        config = cls.CONFIG.from_dict(config.data)
        return config

    @classmethod
    def get_config_or_default(cls) -> SandboxConfig:
        if not cls.is_initialized():
            return cls.get_config_from_env()

        return cls.get_config()

    @classmethod
    def get_db_filepath(cls):
        path = cls.get_config_filepath()
        return os.path.dirname(path)
