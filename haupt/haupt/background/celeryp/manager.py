from haupt.orchestration.crons.deletion import CronsDeletionManager
from haupt.orchestration.crons.heartbeats import CronsHeartbeatManager
from haupt.orchestration.crons.stats import CronsStatsManager
from haupt.orchestration.scheduler.manager import SchedulingManager


class BackgroundManager(
    SchedulingManager,
    CronsDeletionManager,
    CronsHeartbeatManager,
    CronsStatsManager,
):
    pass
