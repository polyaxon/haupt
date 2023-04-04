#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from typing import Dict, Optional, Tuple

from haupt.common.config_manager import ConfigManager
from haupt.common.settings.apps import set_apps
from haupt.common.settings.celery import set_celery
from haupt.common.settings.core import set_core


def set_background_service(
    context,
    config: ConfigManager,
    scheduler_apps: Tuple,
    routes: Dict,
    schedules: Optional[Dict] = None,
    db_app: Optional[str] = None,
):
    set_apps(
        context=context,
        config=config,
        third_party_apps=None,
        project_apps=scheduler_apps,
        db_app=db_app,
    )
    set_core(context=context, config=config, use_db=True)
    set_celery(context=context, config=config, routes=routes, schedules=schedules)


def set_service(context, config: ConfigManager):
    from haupt.background.celeryp.routes import get_routes

    scheduler_apps = ("haupt.background.scheduler.apps.SchedulerConfig",)
    set_background_service(
        context, config, scheduler_apps=scheduler_apps, routes=get_routes(), db_app=None
    )
