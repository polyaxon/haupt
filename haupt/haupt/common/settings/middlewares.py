from haupt.schemas.platform_config import PlatformConfig


def set_middlewares(context, config: PlatformConfig, enable_crsf: bool = False):
    context["MIDDLEWARE"] = (
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.common.CommonMiddleware",
    )

    if enable_crsf:
        context["MIDDLEWARE"] += ("django.middleware.csrf.CsrfViewMiddleware",)

    context["MIDDLEWARE"] += (
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    )

    if context["UI_IN_SANDBOX"]:
        context["MIDDLEWARE"] += ("whitenoise.middleware.WhiteNoiseMiddleware",)


def set_base_middlewares(context, config: PlatformConfig):
    context["MIDDLEWARE"] = ("django.middleware.common.CommonMiddleware",)
    if context["UI_IN_SANDBOX"]:
        context["MIDDLEWARE"] += ("whitenoise.middleware.WhiteNoiseMiddleware",)
