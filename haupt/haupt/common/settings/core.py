#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.config_manager import ConfigManager


def set_core(context, config: ConfigManager, use_db: bool = True):
    context["DEBUG"] = config.is_debug_mode
    context["POLYAXON_SERVICE"] = config.service
    context["POLYAXON_ENVIRONMENT"] = config.env
    context["CHART_VERSION"] = config.chart_version
    context["SCHEDULER_ENABLED"] = config.scheduler_enabled
    context["K8S_NAMESPACE"] = config.namespace

    context["FILE_UPLOAD_PERMISSIONS"] = 0o644

    context["WSGI_APPLICATION"] = "{}.wsgi.application".format(config.config_module)
    context["TIME_ZONE"] = config.timezone
    context["LANGUAGE_CODE"] = "en"
    context["LANGUAGES"] = (("en", "English"),)

    context["USE_I18N"] = True
    context["USE_TZ"] = True

    context["INTERNAL_IPS"] = ("127.0.0.1",)
    context["APPEND_SLASH"] = True

    context["ROOT_URLCONF"] = ""

    if use_db:
        db_engine = (
            "django.db.backends.sqlite3"
            if config.is_sqlite_db_engine
            else "django.db.backends.postgresql"
        )
        context["AUTH_USER_MODEL"] = "db.User"
        context["DB_ENGINE_NAME"] = config.db_engine_name
        context["DEFAULT_DB_ENGINE"] = db_engine
        db_name = config.get("POLYAXON_DB_NAME", "str", is_optional=True)
        if not db_name:
            db_name = "/tmp/plxdb" if config.is_sqlite_db_engine else "polyaxon"
        db_definition = {
            "ENGINE": db_engine,
            "NAME": db_name,
            "USER": config.get("POLYAXON_DB_USER", "str", is_optional=True),
            "PASSWORD": config.get(
                "POLYAXON_DB_PASSWORD", "str", is_secret=True, is_optional=True
            ),
            "HOST": config.get("POLYAXON_DB_HOST", "str", is_optional=True),
            "PORT": config.get("POLYAXON_DB_PORT", "str", is_optional=True),
            "ATOMIC_REQUESTS": True,
            "CONN_MAX_AGE": config.get(
                "POLYAXON_DB_CONN_MAX_AGE",
                "int",
                is_optional=True,
                default=60,
            ),
        }
        db_options = config.get(
            "POLYAXON_DB_OPTIONS", "dict", is_optional=True, default={}
        )
        if db_options:
            db_definition["OPTIONS"] = db_options
        context["DATABASES"] = {"default": db_definition}
