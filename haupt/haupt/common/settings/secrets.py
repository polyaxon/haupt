from haupt.schemas.platform_config import PlatformConfig


def set_secrets(context, config: PlatformConfig):
    context["SECRET_KEY"] = config.secret_key
    context["SECRET_INTERNAL_TOKEN"] = config.secret_internal_token
