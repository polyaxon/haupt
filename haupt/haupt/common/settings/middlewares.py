#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.config_manager import ConfigManager


def set_middlewares(context, config: ConfigManager):
    context["MIDDLEWARE"] = (
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.common.CommonMiddleware",
    )

    if not context["UI_IN_SANDBOX"]:
        context["MIDDLEWARE"] += ("django.middleware.csrf.CsrfViewMiddleware",)

    context["MIDDLEWARE"] += (
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    )

    if context["UI_IN_SANDBOX"]:
        context["MIDDLEWARE"] += ("whitenoise.middleware.WhiteNoiseMiddleware",)


def set_base_middlewares(context, config: ConfigManager):
    context["MIDDLEWARE"] = ("django.middleware.common.CommonMiddleware",)
    if context["UI_IN_SANDBOX"]:
        context["MIDDLEWARE"] += ("whitenoise.middleware.WhiteNoiseMiddleware",)
