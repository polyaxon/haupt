from typing import Optional, Tuple

from clipped.utils.enums import PEnum

from haupt.common.options.exceptions import OptionException
from polyaxon._config.parser import ConfigParser

NAMESPACE_DB_OPTION_MARKER = ":"
NAMESPACE_DB_CONFIG_MARKER = "__"
NAMESPACE_SETTINGS_MARKER = "__"
NAMESPACE_ENV_MARKER = ":"


class OptionStores(str, PEnum):
    ENV = "env"
    DB_OPTION = "db_option"
    DB_CONFIG = "db_config"
    SETTINGS = "settings"


class OptionScope(str, PEnum):
    GLOBAL = "global"
    ORGANISATION = "organization"
    TEAM = "team"
    PROJECT = "project"
    USER = "user"


class Option:
    key = None
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    store = None
    typing = None
    default = None
    options = None
    description = None
    cache_ttl = 0

    @staticmethod
    def get_default_value():
        return None

    @classmethod
    def default_value(cls):
        return cls.default if cls.default is not None else cls.get_default_value()

    @classmethod
    def is_global(cls):
        return cls.scope == OptionScope.GLOBAL

    @classmethod
    def get_marker(cls) -> str:
        if cls.store == OptionStores.DB_OPTION:
            return NAMESPACE_DB_OPTION_MARKER
        if cls.store == OptionStores.DB_CONFIG:
            return NAMESPACE_DB_CONFIG_MARKER
        if cls.store == OptionStores.SETTINGS:
            return NAMESPACE_SETTINGS_MARKER

        return NAMESPACE_ENV_MARKER

    @classmethod
    def parse_key(cls) -> Tuple[Optional[str], str]:
        marker = cls.get_marker()
        parts = cls.key.split(marker)
        if len(parts) > 2:
            raise OptionException(
                "Option declared with multi-namespace key `{}`.".format(cls.key)
            )
        if len(parts) == 1:
            return None, cls.key
        return parts[0], parts[1]

    @classmethod
    def get_namespace(cls) -> Optional[str]:
        return cls.parse_key()[0]

    @classmethod
    def get_key_subject(cls):
        return cls.parse_key()[1]

    @classmethod
    def to_dict(cls, value=None):
        return {
            "key": cls.key,
            "typing": cls.typing,
            "is_list": cls.is_list,
            "is_secret": cls.is_secret,
            "value": value if value is not None else cls.default,
            "description": cls.description,
        }

    @classmethod
    def _extra_processing(cls, value):
        return value

    @classmethod
    def parse(cls, value):
        _value = ConfigParser.parse(cls.typing)(
            key=cls.key,
            value=value,
            is_list=cls.is_list,
            is_optional=cls.is_optional,
            default=cls.default,
            options=cls.options,
        )
        return cls._extra_processing(_value)
