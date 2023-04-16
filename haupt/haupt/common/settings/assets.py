#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.config_manager import ConfigManager
from polyaxon.api import STATIC_V1
from polyaxon.env_vars.keys import (
    EV_KEYS_ARTIFACTS_ROOT,
    EV_KEYS_STATIC_ROOT,
    EV_KEYS_STATIC_URL,
)


def set_assets(context, config: ConfigManager):
    context["MEDIA_ROOT"] = config.get(
        "POLYAXON_MEDIA_ROOT", "str", is_optional=True, default=""
    )
    context["MEDIA_URL"] = config.get(
        "POLYAXON_MEDIA_URL", "str", is_optional=True, default=""
    )

    context["STATIC_ROOT"] = config.get(
        EV_KEYS_STATIC_ROOT,
        "str",
        is_optional=True,
        default=str(config.root_dir / "static"),
    )
    context["STATIC_URL"] = config.get(
        EV_KEYS_STATIC_URL,
        "str",
        is_optional=True,
        default="/static/",
    )

    # Additional locations of static files
    context["STATICFILES_DIRS"] = (str(config.root_dir / "public"),)

    context["STATICFILES_FINDERS"] = (
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    )

    context["LOCALE_PATHS"] = (
        str(config.root_dir / "locale"),
        str(config.root_dir / "client" / "js" / "libs" / "locale"),
    )

    context["STATICI18N_ROOT"] = STATIC_V1
    context["STATICI18N_OUTPUT_DIR"] = "jsi18n"

    context["ARTIFACTS_ROOT"] = config.get(
        EV_KEYS_ARTIFACTS_ROOT,
        "str",
        is_optional=True,
        default="/tmp/plx/artifacts_uploads",
    )
    context["ARCHIVES_ROOT"] = config.get(
        "POLYAXON_ARCHIVES_ROOT",
        "str",
        is_optional=True,
        default="/tmp/plx/archives",
    )
