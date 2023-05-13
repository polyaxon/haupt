from haupt.schemas.platform_config import PlatformConfig


def set_encryption(context, config: PlatformConfig):
    context["ENCRYPTION_KEY"] = config.encryption_key
    context["ENCRYPTION_SECRET"] = config.encryption_secret
    context["ENCRYPTION_BACKEND"] = config.encryption_backend
