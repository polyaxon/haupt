#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from typing import List, Optional

from haupt.common.config_manager import ConfigManager
from polyaxon.env_vars.keys import (
    EV_KEYS_PLATFORM_HOST,
    EV_KEYS_UI_ADMIN_ENABLED,
    EV_KEYS_UI_ASSETS_VERSION,
    EV_KEYS_UI_BASE_URL,
    EV_KEYS_UI_ENABLED,
    EV_KEYS_UI_IN_SANDBOX,
    EV_KEYS_UI_OFFLINE,
)


def set_ui(context, config: ConfigManager, processors: Optional[List[str]] = None):
    context["ROOT_URLCONF"] = "{}.urls".format(config.config_module)
    platform_host = config.get(EV_KEYS_PLATFORM_HOST, "str", is_optional=True)
    context["PLATFORM_HOST"] = platform_host

    def get_allowed_hosts():
        allowed_hosts = config.get(
            "POLYAXON_ALLOWED_HOSTS",
            "str",
            is_optional=True,
            is_list=True,
            default=["*"],
        )  # type: list
        if platform_host:
            allowed_hosts.append(platform_host)
        if ".polyaxon.com" not in allowed_hosts:
            allowed_hosts.append(".polyaxon.com")
        pod_ip = config.get("POLYAXON_POD_IP", "str", is_optional=True)
        if pod_ip:
            allowed_hosts.append(pod_ip)
        host_ip = config.get("POLYAXON_HOST_IP", "str", is_optional=True)
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

    context["FRONTEND_DEBUG"] = config.get(
        "POLYAXON_FRONTEND_DEBUG", "bool", is_optional=True, default=False
    )

    template_debug = (
        config.get("DJANGO_TEMPLATE_DEBUG", "bool", is_optional=True)
        or config.is_debug_mode
    )
    context["UI_ADMIN_ENABLED"] = config.get(
        EV_KEYS_UI_ADMIN_ENABLED, "bool", is_optional=True, default=False
    )
    base_url = config.get(EV_KEYS_UI_BASE_URL, "str", is_optional=True)
    if base_url:
        context["UI_BASE_URL"] = base_url
        context["FORCE_SCRIPT_NAME"] = base_url
    else:
        context["UI_BASE_URL"] = "/"
    context["UI_ASSETS_VERSION"] = config.get(
        EV_KEYS_UI_ASSETS_VERSION, "str", is_optional=True, default=""
    )
    context["UI_OFFLINE"] = config.get(
        EV_KEYS_UI_OFFLINE, "bool", is_optional=True, default=False
    )
    context["UI_ENABLED"] = config.get(
        EV_KEYS_UI_ENABLED, "bool", is_optional=True, default=True
    )
    context["UI_IN_SANDBOX"] = config.get(
        EV_KEYS_UI_IN_SANDBOX, "bool", is_optional=True, default=False
    )
    context["TEMPLATES_DEBUG"] = template_debug
    context["LIST_TEMPLATE_CONTEXT_PROCESSORS"] = processors
    context["TEMPLATES"] = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
            "OPTIONS": {"debug": template_debug, "context_processors": processors},
        }
    ]
