import os

from pathlib import Path

from haupt.schemas.platform_config import PlatformConfig
from polyaxon._config.manager import ConfigManager
from polyaxon._config.spec import ConfigSpec
from polyaxon._env_vars.keys import ENV_KEYS_PLATFORM_CONFIG


class PlatformManager(ConfigManager):
    """Manages platform configuration file."""

    VISIBILITY = ConfigManager.Visibility.GLOBAL
    CONFIG_FILE_NAME = ".platform"
    CONFIG = PlatformConfig
    PERSIST_FORMAT = "yaml"

    @classmethod
    def get_config_from_env(cls, **kwargs) -> PlatformConfig:
        def base_directory():
            root = Path(os.path.abspath(kwargs.get("file_path", __file__)))
            root.resolve()
            return root.parent.parent

        root_dir = base_directory()

        config_module = "polyconf"
        config_prefix = os.environ.get("CONFIG_PREFIX")
        if config_prefix:
            config_module = "{}.{}".format(config_prefix, config_module)
        glob_path = cls.get_global_config_path()
        platform_config_path = os.getenv(ENV_KEYS_PLATFORM_CONFIG) or {}
        config_paths = [
            os.environ,
            {
                "POLYAXON_CONFIG_MODULE": config_module,
                "POLYAXON_CONFIG_ROOT_DIR": root_dir,
            },
            ConfigSpec(
                platform_config_path, config_type=".yaml", check_if_exists=False
            ),
            ConfigSpec(glob_path, config_type=".yaml", check_if_exists=False),
        ]

        platform_config = cls._CONFIG_READER.read_configs(config_paths)
        return PlatformConfig.from_dict(platform_config.data)
