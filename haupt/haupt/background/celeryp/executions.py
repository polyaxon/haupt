from typing import Dict

from haupt.background.celeryp.tasks import SchedulerCeleryTasks


class TasksExecutions:
    _MAPPING = None

    @classmethod
    def run(cls, task: str, kwargs: Dict = None, eager_kwargs: Dict = None) -> Dict:
        if cls._MAPPING is None:
            cls._set_mapping()
        kwargs = kwargs or {}
        eager_kwargs = eager_kwargs or {}
        cls._MAPPING[task](**kwargs, **eager_kwargs)

    @classmethod
    def _set_mapping(cls) -> None:
        from haupt.common.checks import health_task
        from haupt.orchestration.scheduler.manager import RunsManager

        cls._MAPPING = {
            SchedulerCeleryTasks.SCHEDULER_HEALTH: health_task.health_task,
            SchedulerCeleryTasks.RUNS_PREPARE: RunsManager.runs_prepare,
            SchedulerCeleryTasks.RUNS_START: RunsManager.runs_start,
            SchedulerCeleryTasks.RUNS_BUILT: RunsManager.runs_built,
            SchedulerCeleryTasks.RUNS_STOP: RunsManager.runs_stop,
            SchedulerCeleryTasks.RUNS_SET_ARTIFACTS: RunsManager.runs_set_artifacts,
            SchedulerCeleryTasks.RUNS_START_IMMEDIATELY: RunsManager.runs_start_immediately,
            SchedulerCeleryTasks.RUNS_NOTIFY_STATUS: RunsManager.runs_notify_status,
            SchedulerCeleryTasks.RUNS_NOTIFY_DONE: RunsManager.runs_notify_done,
            SchedulerCeleryTasks.RUNS_CHECK_PIPELINE: RunsManager.runs_check_pipeline,
            SchedulerCeleryTasks.RUNS_CHECK_ORPHAN_PIPELINE: RunsManager.runs_check_orphan_pipeline,
            SchedulerCeleryTasks.RUNS_CHECK_EARLY_STOPPING: RunsManager.runs_check_early_stopping,
            SchedulerCeleryTasks.RUNS_WAKEUP_SCHEDULE: RunsManager.runs_wakeup_schedule,
            SchedulerCeleryTasks.RUNS_ITERATE: RunsManager.runs_iterate,
            SchedulerCeleryTasks.RUNS_TUNE: RunsManager.runs_tune,
            SchedulerCeleryTasks.DELETE_ARCHIVED_PROJECT: RunsManager.delete_archived_project,
            SchedulerCeleryTasks.DELETE_ARCHIVED_RUN: RunsManager.delete_archived_run,
        }
