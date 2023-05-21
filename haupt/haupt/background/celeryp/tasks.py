class SchedulerCeleryTasks:
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
    RUNS_HOOKS = "runs_hooks"
    RUNS_START_IMMEDIATELY = "runs_start_immediately"
    RUNS_NOTIFY_STATUS = "runs_notify_status"
    RUNS_NOTIFY_DONE = "runs_notify_done"
    RUNS_CHECK_PIPELINE = "runs_check_pipeline"
    RUNS_CHECK_ORPHAN_PIPELINE = "runs_check_orphan_pipeline"
    RUNS_CHECK_EARLY_STOPPING = "runs_check_early_stopping"
    RUNS_WAKEUP_SCHEDULE = "runs_wakeup_schedule"
    RUNS_ITERATE = "runs_iterate"
    RUNS_TUNE = "runs_tune"
    DELETE_ARCHIVED_PROJECT = "delete_archived_project"
    DELETE_ARCHIVED_RUN = "delete_archived_run"
