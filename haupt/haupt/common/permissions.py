from typing import List, Tuple

from django.conf import settings

from clipped.utils.imports import import_string


class PermissionMapping:
    _MAPPING = {}

    @classmethod
    def get(cls, permissions: List[str]) -> Tuple:
        return tuple(
            cls._MAPPING[permission]
            for permission in permissions
            if permission in cls._MAPPING
        )


PERMISSIONS_MAPPING = (
    import_string(settings.PERMISSIONS_MAPPING)
    if settings.PERMISSIONS_MAPPING
    else PermissionMapping
)
