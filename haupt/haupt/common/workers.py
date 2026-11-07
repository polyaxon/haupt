import logging
import os
from typing import Dict, Optional

from django.conf import settings
from django.db import transaction

from clipped.utils.imports import import_string
from haupt.common import conf
from haupt.common.options.registry.core import SCHEDULER_ENABLED


if settings.SCHEDULER_ENABLED:
    from kombu.exceptions import OperationalError

    from haupt.background.celeryp.app import app
    from haupt.background.celeryp.polyaxon_task import HauptTask

    app.Task = HauptTask  # Custom base class for logging

_logger = logging.getLogger("haupt.workers")


def _send_task(task_name: str, kwargs: Optional[Dict], options: Dict):
    # Runs after the request committed: a broker outage must not turn it into a 500.
    try:
        app.send_task(task_name, kwargs=kwargs, **options)
    except OperationalError as e:
        _logger.warning(
            "Broker unavailable, dropping task: task=%s error=%s", task_name, e
        )


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
    return transaction.on_commit(lambda: _send_task(task_name, kwargs, options))
