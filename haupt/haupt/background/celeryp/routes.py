from haupt.background.celeryp.queues import CeleryQueues
from haupt.background.celeryp.tasks import SchedulerCeleryTasks

SCHEDULER_CORE_ROUTES = {
    # Scheduler health
    SchedulerCeleryTasks.SCHEDULER_HEALTH: {"queue": CeleryQueues.SCHEDULER_HEALTH},
    # compiler
    SchedulerCeleryTasks.RUNS_PREPARE: {"queue": CeleryQueues.SCHEDULER_COMPILER},
    SchedulerCeleryTasks.RUNS_START: {"queue": CeleryQueues.SCHEDULER_COMPILER},
    SchedulerCeleryTasks.RUNS_BUILT: {"queue": CeleryQueues.SCHEDULER_COMPILER},
    # Scheduler runs
    SchedulerCeleryTasks.RUNS_STOP: {"queue": CeleryQueues.SCHEDULER_RUNS},
    SchedulerCeleryTasks.RUNS_HOOKS: {"queue": CeleryQueues.SCHEDULER_RUNS},
    # Scheduler artifacts
    SchedulerCeleryTasks.RUNS_SET_ARTIFACTS: {
        "queue": CeleryQueues.SCHEDULER_ARTIFACTS,
        "priority": 0,
    },
}


def get_routes():
    routes = {}
    routes.update(SCHEDULER_CORE_ROUTES)
    return routes
