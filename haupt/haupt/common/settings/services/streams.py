#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from haupt.common.config_manager import ConfigManager
from haupt.common.settings.apps import set_apps
from haupt.common.settings.assets import set_assets
from haupt.common.settings.core import set_core
from haupt.common.settings.cors import set_cors
from haupt.common.settings.middlewares import set_base_middlewares
from haupt.common.settings.ui import set_ui


def set_streams_apps(context, config: ConfigManager):
    set_apps(
        context=context,
        config=config,
        third_party_apps=("rest_framework", "corsheaders"),
        project_apps=(
            "haupt.common.apis.apps.CommonApisConfig",
            "haupt.streams.apps.StreamsConfig",
        ),
        use_db_apps=False,
        use_staticfiles_app=False,
    )


def set_service(context, config: ConfigManager):
    set_streams_apps(context, config)
    set_core(context=context, config=config, use_db=False)
    set_cors(context=context, config=config)
    set_ui(context=context, config=config)
    set_base_middlewares(context=context, config=config)
    set_assets(context=context, root_dir=config.config_root_dir, config=config)
