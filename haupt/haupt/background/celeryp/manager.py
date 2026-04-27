from haupt.orchestration.crons.cleaning import CronsCleaningManager
from haupt.orchestration.crons.deletion import CronsDeletionManager
from haupt.orchestration.crons.heartbeats import CronsHeartbeatManager
from haupt.orchestration.crons.stats import CronsStatsManager
from haupt.orchestration.scheduler.manager import SchedulingManager


class BackgroundManager(
    SchedulingManager,
    CronsCleaningManager,
    CronsDeletionManager,
    CronsHeartbeatManager,
    CronsStatsManager,
):
    pass
