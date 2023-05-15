from haupt.background.celeryp.queues import CeleryCoreQueues
from haupt.background.celeryp.tasks import SchedulerCeleryTasks

SCHEDULER_CORE_ROUTES = {
    # Scheduler health
    SchedulerCeleryTasks.SCHEDULER_HEALTH: {"queue": CeleryCoreQueues.SCHEDULER_HEALTH},
    # compiler
    SchedulerCeleryTasks.RUNS_PREPARE: {"queue": CeleryCoreQueues.SCHEDULER_COMPILER},
    SchedulerCeleryTasks.RUNS_START: {"queue": CeleryCoreQueues.SCHEDULER_COMPILER},
    SchedulerCeleryTasks.RUNS_BUILT: {"queue": CeleryCoreQueues.SCHEDULER_COMPILER},
    # Scheduler runs
    SchedulerCeleryTasks.RUNS_STOP: {"queue": CeleryCoreQueues.SCHEDULER_RUNS},
    SchedulerCeleryTasks.RUNS_HOOKS: {"queue": CeleryCoreQueues.SCHEDULER_RUNS},
    # Scheduler artifacts
    SchedulerCeleryTasks.RUNS_SET_ARTIFACTS: {
        "queue": CeleryCoreQueues.SCHEDULER_ARTIFACTS,
        "priority": 0,
    },
}


def get_routes():
    routes = {}
    routes.update(SCHEDULER_CORE_ROUTES)
    return routes
