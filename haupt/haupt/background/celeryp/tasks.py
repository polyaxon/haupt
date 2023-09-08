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
    STATS_CALCULATION_PROJECT = "stats_calculation_project"


class CronsCeleryTasks:
    """Crons celery tasks.

    N.B. make sure that the task name is not < 128.
    """

    CRONS_HEALTH = "crons_health"

    DELETE_ARCHIVED_PROJECTS = "delete_archived_projects"
    DELETE_IN_PROGRESS_PROJECTS = "delete_in_progress_projects"
    DELETE_ARCHIVED_RUNS = "delete_archived_runs"
    DELETE_IN_PROGRESS_RUNS = "delete_in_progress_runs"

    STATS_CALCULATION_PROJECTS = "stats_calculation_projects"

    HEARTBEAT_RUNS = "heartbeat_runs"
    HEARTBEAT_OUT_OF_SYNC_SCHEDULES = "heartbeat_out_of_sync_schedules"
    HEARTBEAT_STOPPING_RUNS = "heartbeat_stopping_runs"
    HEARTBEAT_PROJECT_LAST_UPDATED = "heartbeat_project_last_updated"
