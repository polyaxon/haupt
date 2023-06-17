import logging

from typing import List, Optional

from haupt.schemas.platform_config import PlatformConfig


def set_ui(context, config: PlatformConfig, processors: Optional[List[str]] = None):
    logging.debug(config.config_module)
    context["ROOT_URLCONF"] = "{}.urls".format(config.config_module)
    platform_host = config.platform_host
    context["PLATFORM_HOST"] = platform_host

    def get_allowed_hosts():
        allowed_hosts = config.allowed_hosts
        if platform_host:
            allowed_hosts.append(platform_host)
        if ".polyaxon.com" not in allowed_hosts:
            allowed_hosts.append(".polyaxon.com")
        pod_ip = config.pod_ip
        if pod_ip:
            allowed_hosts.append(pod_ip)
        host_ip = config.host_ip
        if host_ip:
            host_cidr = ".".join(host_ip.split(".")[:-1])
            allowed_hosts += ["{}.{}".format(host_cidr, i) for i in range(255)]

        return allowed_hosts

    context["ALLOWED_HOSTS"] = get_allowed_hosts()

    processors = processors or []
    if not config.is_streams_service:
        processors = [
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ] + processors
    processors = [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.template.context_processors.media",
        "django.template.context_processors.static",
        "django.template.context_processors.tz",
        "haupt.common.settings.context_processors.version",
        "haupt.common.settings.context_processors.ui_assets_version",
        "haupt.common.settings.context_processors.ui_base_url",
        "haupt.common.settings.context_processors.ui_offline",
        "haupt.common.settings.context_processors.ui_enabled",
        "haupt.common.settings.context_processors.ui_in_sandbox",
    ] + processors

    context["FRONTEND_DEBUG"] = config.frontend_debug

    template_debug = config.template_debug or config.is_debug_mode
    context["UI_ADMIN_ENABLED"] = config.ui_admin_enabled
    base_url = config.ui_base_url
    if base_url:
        context["UI_BASE_URL"] = base_url
        context["FORCE_SCRIPT_NAME"] = base_url
    else:
        context["UI_BASE_URL"] = "/"
    context["UI_ASSETS_VERSION"] = config.ui_assets_version
    context["UI_OFFLINE"] = config.ui_offline
    context["UI_ENABLED"] = config.ui_enabled
    context["UI_IN_SANDBOX"] = config.ui_in_sandbox
    context["TEMPLATES_DEBUG"] = template_debug
    context["LIST_TEMPLATE_CONTEXT_PROCESSORS"] = processors
    context["TEMPLATES"] = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
            "OPTIONS": {"debug": template_debug, "context_processors": processors},
        }
    ]
