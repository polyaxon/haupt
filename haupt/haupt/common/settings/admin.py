from haupt.schemas.platform_config import PlatformConfig


def set_admin(context, config: PlatformConfig):
    if config.admin_mail and config.admin_mail:
        admins = ((config.admin_name, config.admin_mail),)
        context["ADMINS"] = admins
        context["MANAGERS"] = admins
