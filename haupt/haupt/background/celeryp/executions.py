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
        from haupt.orchestration.scheduler.manager import SchedulingManager

        cls._MAPPING = {
            SchedulerCeleryTasks.SCHEDULER_HEALTH: health_task.health_task,
            SchedulerCeleryTasks.RUNS_PREPARE: SchedulingManager.runs_prepare,
            SchedulerCeleryTasks.RUNS_START: SchedulingManager.runs_start,
            SchedulerCeleryTasks.RUNS_BUILT: SchedulingManager.runs_built,
            SchedulerCeleryTasks.RUNS_STOP: SchedulingManager.runs_stop,
            SchedulerCeleryTasks.RUNS_SET_ARTIFACTS: SchedulingManager.runs_set_artifacts,
            SchedulerCeleryTasks.RUNS_START_IMMEDIATELY: SchedulingManager.runs_start_immediately,
            SchedulerCeleryTasks.RUNS_NOTIFY_STATUS: SchedulingManager.runs_notify_status,
            SchedulerCeleryTasks.RUNS_NOTIFY_DONE: SchedulingManager.runs_notify_done,
            SchedulerCeleryTasks.RUNS_CHECK_PIPELINE: SchedulingManager.runs_check_pipeline,
            SchedulerCeleryTasks.RUNS_CHECK_ORPHAN_PIPELINE: SchedulingManager.runs_check_orphan_pipeline,
            SchedulerCeleryTasks.RUNS_CHECK_EARLY_STOPPING: SchedulingManager.runs_check_early_stopping,
            SchedulerCeleryTasks.RUNS_WAKEUP_SCHEDULE: SchedulingManager.runs_wakeup_schedule,
            SchedulerCeleryTasks.RUNS_ITERATE: SchedulingManager.runs_iterate,
            SchedulerCeleryTasks.RUNS_TUNE: SchedulingManager.runs_tune,
            SchedulerCeleryTasks.DELETE_ARCHIVED_PROJECT: SchedulingManager.delete_archived_project,
            SchedulerCeleryTasks.DELETE_ARCHIVED_RUN: SchedulingManager.delete_archived_run,
        }
