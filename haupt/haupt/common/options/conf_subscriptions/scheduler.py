from haupt.common import conf
from haupt.common.options.registry import scheduler

conf.subscribe(scheduler.SchedulerCountdown)
