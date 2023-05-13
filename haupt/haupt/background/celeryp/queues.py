class CeleryCoreQueues:
    """Celery Core Queues.

    N.B. make sure that the queue name is not < 128.
    """

    SCHEDULER_HEALTH = "queues.scheduler.health"
    SCHEDULER_RUNS = "queues.scheduler.runs"
    SCHEDULER_COMPILER = "queues.scheduler.compiler"
    SCHEDULER_ARTIFACTS = "queues.scheduler.artifacts"
    SCHEDULER_CLEAN = "queues.scheduler.clean"

    ALL_QUEUES = (
        SCHEDULER_HEALTH,
        SCHEDULER_RUNS,
        SCHEDULER_COMPILER,
        SCHEDULER_ARTIFACTS,
        SCHEDULER_CLEAN,
    )
