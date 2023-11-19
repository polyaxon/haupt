class CeleryQueues:
    """Celery Queues.

    N.B. make sure that the queue name is not < 128.
    """

    SCHEDULER_HEALTH = "queues.scheduler.health"
    SCHEDULER_RUNS = "queues.scheduler.runs"
    SCHEDULER_COMPILER = "queues.scheduler.compiler"
    SCHEDULER_ARTIFACTS = "queues.scheduler.artifacts"
    SCHEDULER_CLEAN = "queues.scheduler.clean"

    @classmethod
    def scheduler(cls):
        return f"{cls.SCHEDULER_HEALTH},{cls.SCHEDULER_COMPILER},{cls.SCHEDULER_RUNS},{cls.SCHEDULER_ARTIFACTS},{cls.SCHEDULER_CLEAN}"

    @classmethod
    def all(cls):
        return cls.scheduler()
