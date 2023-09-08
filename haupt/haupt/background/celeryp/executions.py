from typing import Dict

from haupt.background.celeryp.tasks import CronsCeleryTasks, SchedulerCeleryTasks


class TasksExecutions:
    _MAPPING = None
    _MANAGER = None

    @classmethod
    def get_mapping(cls):
        if cls._MAPPING is None:
            cls._set_mapping()
        return cls._MAPPING

    @classmethod
    def get_manager(cls):
        if cls._MANAGER is None:
            cls._set_manager()
        return cls._MANAGER

    @classmethod
    def run(cls, task: str, kwargs: Dict = None, eager_kwargs: Dict = None) -> Dict:
        kwargs = kwargs or {}
        eager_kwargs = eager_kwargs or {}
        mapping = cls.get_mapping()
        mapping[task](**kwargs, **eager_kwargs)

    @classmethod
    def register_tasks(cls):
        from haupt.common import workers

        mapping = cls.get_mapping()
        for task in mapping:
            workers.app.task(name=task, ignore_result=True)(mapping[task])

    @classmethod
    def _set_manager(cls):
        from haupt.background.celeryp.manager import BackgroundManager

        cls._MANAGER = BackgroundManager

    @classmethod
    def _set_mapping(cls):
        from haupt.common.checks import health_task

        manager = cls.get_manager()

        cls._MAPPING = {
            SchedulerCeleryTasks.STATS_CALCULATION_PROJECT: manager.stats_calculation_project,
            SchedulerCeleryTasks.SCHEDULER_HEALTH: health_task.health_task,
            SchedulerCeleryTasks.RUNS_PREPARE: manager.runs_prepare,
            SchedulerCeleryTasks.RUNS_HOOKS: manager.runs_hooks,
            SchedulerCeleryTasks.RUNS_START_IMMEDIATELY: manager.runs_start_immediately,
            SchedulerCeleryTasks.RUNS_START: manager.runs_start,
            SchedulerCeleryTasks.RUNS_BUILT: manager.runs_built,
            SchedulerCeleryTasks.RUNS_STOP: manager.runs_stop,
            SchedulerCeleryTasks.RUNS_SET_ARTIFACTS: manager.runs_set_artifacts,
            SchedulerCeleryTasks.RUNS_NOTIFY_STATUS: manager.runs_notify_status,
            SchedulerCeleryTasks.RUNS_NOTIFY_DONE: manager.runs_notify_done,
            SchedulerCeleryTasks.RUNS_CHECK_PIPELINE: manager.runs_check_pipeline,
            SchedulerCeleryTasks.RUNS_CHECK_ORPHAN_PIPELINE: manager.runs_check_orphan_pipeline,
            SchedulerCeleryTasks.RUNS_CHECK_EARLY_STOPPING: manager.runs_check_early_stopping,
            SchedulerCeleryTasks.RUNS_WAKEUP_SCHEDULE: manager.runs_wakeup_schedule,
            SchedulerCeleryTasks.RUNS_ITERATE: manager.runs_iterate,
            SchedulerCeleryTasks.RUNS_TUNE: manager.runs_tune,
            SchedulerCeleryTasks.DELETE_ARCHIVED_PROJECT: manager.delete_archived_project,
            SchedulerCeleryTasks.DELETE_ARCHIVED_RUN: manager.delete_archived_run,
            CronsCeleryTasks.CRONS_HEALTH: health_task.health_task,
            CronsCeleryTasks.DELETE_ARCHIVED_PROJECTS: manager.delete_archived_projects,
            CronsCeleryTasks.DELETE_IN_PROGRESS_PROJECTS: manager.delete_in_progress_projects,
            CronsCeleryTasks.DELETE_ARCHIVED_RUNS: manager.delete_archived_runs,
            CronsCeleryTasks.DELETE_IN_PROGRESS_RUNS: manager.delete_in_progress_runs,
            CronsCeleryTasks.HEARTBEAT_OUT_OF_SYNC_SCHEDULES: manager.heartbeat_out_of_sync_schedules,
            CronsCeleryTasks.HEARTBEAT_STOPPING_RUNS: manager.heartbeat_stopping_runs,
            CronsCeleryTasks.HEARTBEAT_PROJECT_LAST_UPDATED: manager.heartbeat_project_last_updated,
            CronsCeleryTasks.STATS_CALCULATION_PROJECTS: manager.stats_calculation_projects,
        }
