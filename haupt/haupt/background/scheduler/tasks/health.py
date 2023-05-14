from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.common import workers
from haupt.common.checks import health_task


@workers.app.task(name=SchedulerCeleryTasks.SCHEDULER_HEALTH, ignore_result=False)
def scheduler_health(x, y):
    return health_task.health_task(x, y)
