from typing import Optional, Tuple

from django.conf import settings

from haupt.common.options.exceptions import OptionException
from haupt.common.options.option import (
    NAMESPACE_DB_OPTION_MARKER,
    Option,
    OptionScope,
    OptionStores,
)
from haupt.common.options.option_namespaces import FEATURES


class Feature(Option):
    scope = OptionScope.USER
    is_secret = False
    is_optional = True
    is_list = False
    store = OptionStores(settings.STORE_OPTION)
    typing = "bool"
    default = True
    options = [True, False]
    immutable = False  # If immutable, the feature cannot be update by the user
    description = None

    @classmethod
    def get_marker(cls) -> str:
        return NAMESPACE_DB_OPTION_MARKER

    @classmethod
    def parse_key(cls) -> Tuple[Optional[str], str]:
        marker = cls.get_marker()
        parts = cls.key.split(marker)
        # First part is a Meta namespace `features`
        if len(parts) > 3 or len(parts) < 1:  # pylint:disable=len-as-condition
            raise OptionException(
                "Feature declared with multi-namespace key `{}`.".format(cls.key)
            )
        if parts[0] != FEATURES:
            raise OptionException(
                "Feature declared with wrong namespace key `{}`.".format(cls.key)
            )
        if len(parts) == 2:
            return None, parts[1]
        return parts[1], parts[2]

    @classmethod
    def get_namespace(cls) -> Optional[str]:
        return cls.parse_key()[0]

    @classmethod
    def get_key_subject(cls):
        return cls.parse_key()[1]
