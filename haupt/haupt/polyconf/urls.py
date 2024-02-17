from haupt.polyconf.settings import PLATFORM_CONFIG

if PLATFORM_CONFIG.is_scheduler_service:
    urlpatterns = []
elif PLATFORM_CONFIG.is_streams_service:
    from haupt.streams.patterns import *  # noqa
else:
    from haupt.apis.patterns import *  # noqa
