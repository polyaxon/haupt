import os

from haupt.schemas.sandbox_config import SandboxConfig
from polyaxon._config.manager import ConfigManager
from polyaxon._config.spec import ConfigSpec


class SandboxConfigManager(ConfigManager):
    """Manages sandbox configuration .sandbox file."""

    VISIBILITY = ConfigManager.Visibility.ALL
    CONFIG_FILE_NAME = ".sandbox"
    CONFIG = SandboxConfig
    PERSIST_FORMAT = "yaml"

    @classmethod
    def get_config_from_env(cls):
        glob_path = cls.get_global_config_path()
        config_paths = [
            ConfigSpec(glob_path, config_type=".yaml", check_if_exists=False),
            os.environ,
            {"dummy": "dummy"},
        ]

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
