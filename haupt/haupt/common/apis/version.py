from haupt import settings
from haupt.common import conf
from haupt.common.options.registry.installation import (
    ORGANIZATION_ID,
    PLATFORM_DIST,
    PLATFORM_MODE,
    PLATFORM_VERSION,
)


def get_version():
    data = {
        "key": conf.get(ORGANIZATION_ID),
        "version": conf.get(PLATFORM_VERSION),
        "dist": conf.get(PLATFORM_DIST),
        "mode": conf.get(PLATFORM_MODE),
    }
    if settings.SANDBOX_CONFIG:
        data["mode"] = settings.SANDBOX_CONFIG.mode

    return data
