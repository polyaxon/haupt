#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from corsheaders.defaults import default_headers

from haupt.common.config_manager import ConfigManager
from polyaxon.services.headers import PolyaxonServiceHeaders


def set_cors(context, config: ConfigManager):
    # session settings
    context["CORS_ALLOW_CREDENTIALS"] = True
    allowed_list = config.get(
        "POLYAXON_CORS_ALLOWED_ORIGINS", "list", is_optional=True, default=[]
    )
    context["CORS_ALLOWED_ORIGINS"] = allowed_list
    context["CORS_ALLOW_ALL_ORIGINS"] = False if allowed_list else True

    context["CORS_ALLOW_HEADERS"] = (
        default_headers + PolyaxonServiceHeaders.get_headers()
    )

    ssl_enabled = config.get(
        "POLYAXON_SSL_ENABLED", "bool", is_optional=True, default=False
    )
    ssl_redirect_enabled = config.get(
        "POLYAXON_SSL_REDIRECT_ENABLED", "bool", is_optional=True, default=False
    )
    context["SSL_ENABLED"] = ssl_enabled
    context["PROTOCOL"] = "http"
    context["WS_PROTOCOL"] = "ws"
    if ssl_enabled:
        context["SESSION_COOKIE_SECURE"] = True
        context["CSRF_COOKIE_SECURE"] = True
        context["SECURE_PROXY_SSL_HEADER"] = ("HTTP_X_FORWARDED_PROTO", "https")
        context["PROTOCOL"] = "https"
        context["WS_PROTOCOL"] = "wss"
    if ssl_redirect_enabled:
        context["SECURE_SSL_REDIRECT"] = True
