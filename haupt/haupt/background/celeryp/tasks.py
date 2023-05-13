class CoreSchedulerCeleryTasks:
    """Scheduler celery tasks.

    N.B. make sure that the task name is not < 128.
    """

    SCHEDULER_HEALTH = "scheduler_health"

    RUNS_PREPARE = "runs_prepare"
    RUNS_START = "runs_start"
    RUNS_BUILT = "runs_built"
    RUNS_STOP = "runs_stop"
    RUNS_DELETE = "runs_delete"
    RUNS_SET_ARTIFACTS = "runs_set_artifacts"
