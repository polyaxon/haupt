#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.config_manager import ConfigManager
from haupt.common.settings.apps import set_apps
from haupt.common.settings.core import set_core


def set_platform_apps(context, config: ConfigManager):
    set_apps(
        context=context,
        config=config,
        third_party_apps=("rest_framework", "corsheaders"),
        project_apps=(
            "haupt.common.apis.apps.CommonApisConfig",
            "django.contrib.admin",
            "django.contrib.admindocs",
            "haupt.apis.apps.APIsConfig",
            "haupt.streams.apps.StreamsConfig",
            "haupt.common.commands.apps.CommandsConfig",
        ),
        use_db_apps=True,
        use_staticfiles_app=True,
    )


def set_app(context, config: ConfigManager):
    set_platform_apps(context, config)
    set_core(context=context, config=config, use_db=True)
