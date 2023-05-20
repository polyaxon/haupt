import logging

from typing import Dict, List

from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.common import workers
from haupt.orchestration.scheduler.manager import RunsManager

_logger = logging.getLogger("polyaxon.scheduler")


@workers.app.task(name=SchedulerCeleryTasks.RUNS_PREPARE, ignore_result=True)
def runs_prepare(run_id):
    RunsManager.runs_prepare(run_id=run_id, run=None, start=True)


@workers.app.task(name=SchedulerCeleryTasks.RUNS_HOOKS, ignore_result=True)
def runs_hooks(run_id):
    RunsManager.runs_hooks(run_id=run_id, run=None)


@workers.app.task(name=SchedulerCeleryTasks.RUNS_START_IMMEDIATELY, ignore_result=True)
def runs_start_immediately(run_id):
    RunsManager.runs_start_immediately(run_id=run_id, run=None)


@workers.app.task(name=SchedulerCeleryTasks.RUNS_START, ignore_result=True)
def runs_start(run_id):
    RunsManager.runs_start(run_id=run_id, run=None)


@workers.app.task(name=SchedulerCeleryTasks.RUNS_BUILT, ignore_result=True)
def runs_built(run_id):
    RunsManager.runs_built(run_id=run_id, run=None)


@workers.app.task(name=SchedulerCeleryTasks.RUNS_SET_ARTIFACTS, ignore_result=True)
def runs_set_artifacts(run_id, artifacts: List[Dict]):
    RunsManager.runs_set_artifacts(run_id=run_id, run=None, artifacts=artifacts)


@workers.app.task(name=SchedulerCeleryTasks.RUNS_ITERATE, ignore_result=True)
def runs_iterate(run_id):
    RunsManager.runs_iterate(run_id=run_id, run=None)


@workers.app.task(name=SchedulerCeleryTasks.RUNS_TUNE, ignore_result=True)
def runs_tune(run_id):
    RunsManager.runs_tune(run_id=run_id, run=None)


@workers.app.task(
    name=SchedulerCeleryTasks.RUNS_CHECK_EARLY_STOPPING, ignore_result=True
)
def runs_check_early_stopping(run_id):
    RunsManager.runs_check_early_stopping(run_id=run_id, run=None)


@workers.app.task(name=SchedulerCeleryTasks.RUNS_WAKEUP_SCHEDULE, ignore_result=True)
def runs_wakeup_schedule(run_id):
    RunsManager.runs_wakeup_schedule(run_id=run_id, run=None)


@workers.app.task(name=SchedulerCeleryTasks.RUNS_NOTIFY_DONE, ignore_result=True)
def runs_notify_done(run_id):
    RunsManager.runs_notify_done(run_id=run_id, run=None)


@workers.app.task(name=SchedulerCeleryTasks.RUNS_NOTIFY_STATUS, ignore_result=True)
def runs_notify_status(run_id):
    RunsManager.runs_notify_status(run_id=run_id, run=None)


@workers.app.task(name=SchedulerCeleryTasks.RUNS_CHECK_PIPELINE, ignore_result=True)
def runs_check_pipeline(run_id):
    RunsManager.runs_check_pipeline(run_id=run_id, run=None)


@workers.app.task(
    name=SchedulerCeleryTasks.RUNS_CHECK_ORPHAN_PIPELINE, ignore_result=True
)
def runs_check_orphan_pipeline(run_id):
    RunsManager.runs_check_orphan_pipeline(run_id=run_id, run=None)
