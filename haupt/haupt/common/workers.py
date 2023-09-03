import os

from typing import Dict, Optional

from clipped.utils.imports import import_string

from django.conf import settings
from django.db import transaction

from haupt.common import conf
from haupt.common.options.registry.core import SCHEDULER_ENABLED

if settings.SCHEDULER_ENABLED:
    from haupt.background.celeryp.app import app
    from haupt.background.celeryp.polyaxon_task import HauptTask

    app.Task = HauptTask  # Custom base class for logging


def send(
    task_name,
    delay: Optional[bool] = None,
    kwargs: Optional[Dict] = None,
    eager_kwargs: Optional[Dict] = None,
    **options,
):
    delay = conf.get(SCHEDULER_ENABLED) if delay is None else delay
    if not delay:
        module = os.environ.get("CONFIG_PREFIX", "haupt")
        tasks_execution = import_string(
            f"{module}.background.celeryp.executions.TasksExecutions"
        )
        tasks_execution.run(task=task_name, kwargs=kwargs, eager_kwargs=eager_kwargs)
        return
    options["ignore_result"] = options.get("ignore_result", True)
    return transaction.on_commit(
        lambda: app.send_task(task_name, kwargs=kwargs, **options)
    )
    # if "countdown" not in options:
    #     options["countdown"] = conf.get(SCHEDULER_GLOBAL_COUNTDOWN)
    # return app.send_task(task_name, kwargs=kwargs, **options)
