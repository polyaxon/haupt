from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.common import workers
from haupt.db.defs import Models


class CronsCleaningManager:
    @staticmethod
    def clean_stats_projects():
        project_ids = Models.Project.all.values_list("id", flat=True)
        for project_id in project_ids:
            workers.send(
                SchedulerCeleryTasks.CLEAN_STATS_PROJECT,
                kwargs={"project_id": project_id},
            )
