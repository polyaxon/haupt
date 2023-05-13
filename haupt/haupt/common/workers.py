from django.db import transaction

from haupt.background.celeryp.app import app
from haupt.background.celeryp.polyaxon_task import HauptTask

app.Task = HauptTask  # Custom base class for logging


def send(task_name, kwargs=None, **options):
    options["ignore_result"] = options.get("ignore_result", True)
    return transaction.on_commit(
        lambda: app.send_task(task_name, kwargs=kwargs, **options)
    )
    # if "countdown" not in options:
    #     options["countdown"] = conf.get(SCHEDULER_GLOBAL_COUNTDOWN)
    # return app.send_task(task_name, kwargs=kwargs, **options)
