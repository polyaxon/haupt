#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.config_manager import ConfigManager
from polyaxon.api import STATIC_V1
from polyaxon.env_vars.keys import EV_KEYS_STATIC_URL


def set_assets(context, root_dir, config: ConfigManager):
    context["MEDIA_ROOT"] = config.get_string("POLYAXON_MEDIA_ROOT")
    context["MEDIA_URL"] = config.get_string("POLYAXON_MEDIA_URL")

    context["STATIC_ROOT"] = config.get_string("POLYAXON_STATIC_ROOT")
    context["STATIC_URL"] = config.get_string(
        EV_KEYS_STATIC_URL,
        is_optional=True,
        default="/static/",
    )

    # Additional locations of static files
    context["STATICFILES_DIRS"] = (str(root_dir.parent / "public"),)

    context["STATICFILES_FINDERS"] = (
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    )

    context["LOCALE_PATHS"] = (
        str(root_dir / "locale"),
        str(root_dir / "client" / "js" / "libs" / "locale"),
    )

    context["STATICI18N_ROOT"] = STATIC_V1
    context["STATICI18N_OUTPUT_DIR"] = "jsi18n"

    context["ARTIFACTS_ROOT"] = config.get_string(
        "POLYAXON_ARTIFACTS_ROOT",
        is_optional=True,
        default="/tmp/plx/artifacts_uploads",
    )
    context["LOGS_ROOT"] = config.get_string(
        "POLYAXON_LOGS_ROOT", is_optional=True, default="/tmp/plx/logs_uploads"
    )
    context["ARCHIVES_ROOT"] = config.get_string(
        "POLYAXON_ARCHIVES_ROOT", is_optional=True, default="/tmp/plx/archives"
    )