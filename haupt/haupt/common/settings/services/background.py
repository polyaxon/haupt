from typing import Dict, Optional, Tuple

from haupt.common.settings.apps import set_apps
from haupt.common.settings.celery import set_celery
from haupt.common.settings.core import set_core
from haupt.schemas.platform_config import PlatformConfig


def set_background_service(
    context,
    config: PlatformConfig,
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


def set_service(context, config: PlatformConfig):
    from haupt.background.celeryp.routes import get_routes

    scheduler_apps = ("haupt.background.scheduler.apps.SchedulerConfig",)
    set_background_service(
        context, config, scheduler_apps=scheduler_apps, routes=get_routes(), db_app=None
    )
