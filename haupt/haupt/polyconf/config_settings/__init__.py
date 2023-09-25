# isort: skip_file

# Default configs

from haupt.polyconf.config_manager import PLATFORM_CONFIG

from haupt.common.settings.logging import set_logging
from haupt.common.settings.admin import set_admin
from haupt.common.settings.secrets import set_secrets

context = locals()
MAX_CONCURRENCY = PLATFORM_CONFIG.max_concurrency or 1
set_logging(context=context, config=PLATFORM_CONFIG)
set_admin(context=context, config=PLATFORM_CONFIG)
set_secrets(context=context, config=PLATFORM_CONFIG)
if PLATFORM_CONFIG.is_streams_service:
    from haupt.common.settings.services.streams import set_service
elif PLATFORM_CONFIG.is_api_service:
    from haupt.common.settings.services.api import set_service
else:
    from haupt.common.settings.services.background import set_service

set_service(context=context, config=PLATFORM_CONFIG)

from haupt.common.settings.defaults import *

if PLATFORM_CONFIG.is_api_service or PLATFORM_CONFIG.is_streams_service:
    from .rest import *
