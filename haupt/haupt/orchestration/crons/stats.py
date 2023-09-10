from django.db.models import F, Q

from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.common import workers
from haupt.db.defs import Models


class CronsStatsManager:
    @staticmethod
    def stats_calculation_projects():
        projects = Models.Project.objects.filter(
            Q(updated_at__gt=F("latest_stats__updated_at"))
            | Q(latest_stats__isnull=True)
        )
        project_ids = set(projects.values_list("id", flat=True))

        if not project_ids:
            return

        for project_id in project_ids:
            workers.send(
                SchedulerCeleryTasks.STATS_CALCULATION_PROJECT,
                kwargs={"project_id": project_id},
            )
        return project_ids
