from corsheaders.defaults import default_headers

from haupt.schemas.platform_config import PlatformConfig
from polyaxon._services.headers import PolyaxonServiceHeaders


def set_cors(context, config: PlatformConfig):
    # session settings
    context["CORS_ALLOW_CREDENTIALS"] = True
    context["CORS_ALLOWED_ORIGINS"] = config.cors_allowed_origins
    context["CORS_ALLOW_ALL_ORIGINS"] = False if config.cors_allowed_origins else True

    context["CORS_ALLOW_HEADERS"] = (
        default_headers + PolyaxonServiceHeaders.get_headers()
    )

    context["SSL_ENABLED"] = config.ssl_enabled
    context["PROTOCOL"] = "http"
    context["WS_PROTOCOL"] = "ws"
    if config.ssl_enabled:
        context["SESSION_COOKIE_SECURE"] = True
        context["CSRF_COOKIE_SECURE"] = True
        context["SECURE_PROXY_SSL_HEADER"] = ("HTTP_X_FORWARDED_PROTO", "https")
        context["PROTOCOL"] = "https"
        context["WS_PROTOCOL"] = "wss"
    if config.ssl_redirect_enabled:
        context["SECURE_SSL_REDIRECT"] = True
