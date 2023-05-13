from typing import Any

from haupt.common.conf.exceptions import ConfException
from haupt.common.conf.handler import BaseConfHandler
from haupt.common.options.option import Option


class SettingsConfHandler(BaseConfHandler):
    def __init__(self):
        from django.conf import settings

        self.settings = settings

    def get(self, option: Option, **kwargs) -> Any:  # pylint:disable=arguments-differ
        if hasattr(self.settings, option.key):
            return getattr(self.settings, option.key)
        if not option.is_optional:
            raise ConfException(
                "The config option `{}` was not found or not correctly "
                "set on the settings backend.".format(option.key)
            )
        return option.default_value()

    def set(  # pylint:disable=arguments-differ
        self, option: Option, value: Any, **kwargs
    ):
        raise ConfException(
            "The settings backend does not allow to set values, "
            "are you sure the key `{}` was correctly defined.".format(option.key)
        )

    def delete(self, option: Option, **kwargs):  # pylint:disable=arguments-differ
        raise ConfException(
            "The settings backend does not allow to delete values, "
            "are you sure the key `{}` was correctly defined.".format(option.key)
        )
