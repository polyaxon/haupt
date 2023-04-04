#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from typing import Dict, List, Optional, Tuple

from haupt.common.config_manager import ConfigManager
from haupt.common.settings.apps import set_apps
from haupt.common.settings.assets import set_assets
from haupt.common.settings.celery import set_celery
from haupt.common.settings.core import set_core
from haupt.common.settings.cors import set_cors
from haupt.common.settings.middlewares import set_middlewares
from haupt.common.settings.ui import set_ui


def set_api_service(
    context,
    config: ConfigManager,
    api_apps: Tuple,
    routes: Dict,
    db_app: Optional[str] = None,
    processors: Optional[List[str]] = None,
):
    project_apps = (
        "haupt.common.apis.apps.CommonApisConfig",
        "haupt.common.commands.apps.CommandsConfig",
    ) + api_apps
    set_apps(
        context=context,
        config=config,
        third_party_apps=("rest_framework", "corsheaders"),
        project_apps=project_apps,
        db_app=db_app,
        use_db_apps=True,
        use_admin_apps=True,
        use_staticfiles_app=True,
    )
    set_core(context=context, config=config, use_db=True)
    set_cors(context=context, config=config)
    set_ui(context=context, config=config, processors=processors)
    set_middlewares(context=context, config=config)
    set_assets(context=context, config=config)
    if config.scheduler_enabled:
        set_celery(context=context, config=config, routes=routes)


def set_service(context, config: ConfigManager):
    from haupt.background.celeryp.routes import get_routes

    api_apps = (
        "haupt.apis.apps.APIsConfig",
        "haupt.streams.apps.StreamsConfig",
    )
    set_api_service(
        context, config, api_apps=api_apps, routes=get_routes(), db_app=None
    )
