from typing import Dict

from haupt.background.celeryp.tasks import CoreSchedulerCeleryTasks


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
        from haupt.orchestration.scheduler import manager

        cls._MAPPING = {
            CoreSchedulerCeleryTasks.SCHEDULER_HEALTH: health_task.health_task,
            CoreSchedulerCeleryTasks.RUNS_PREPARE: manager.runs_prepare,
            CoreSchedulerCeleryTasks.RUNS_START: manager.runs_start,
            CoreSchedulerCeleryTasks.RUNS_BUILT: manager.runs_built,
            CoreSchedulerCeleryTasks.RUNS_STOP: manager.runs_stop,
            CoreSchedulerCeleryTasks.RUNS_DELETE: manager.runs_delete,
            CoreSchedulerCeleryTasks.RUNS_SET_ARTIFACTS: manager.runs_set_artifacts,
        }
