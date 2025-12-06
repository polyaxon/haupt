from clipped.utils.tz import get_datetime_from_now

from django.db.models import Count, Q

from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.common import workers
from haupt.db.defs import Models
from haupt.db.managers.projects import update_project_based_on_last_updated_entities
from haupt.db.managers.runs import get_stopping_pipelines_with_no_runs
from haupt.db.managers.statuses import bulk_new_run_status
from polyaxon.schemas import LifeCycle, V1RunKind, V1StatusCondition, V1Statuses


class CronsHeartbeatManager:
    @staticmethod
    def heartbeat_out_of_sync_schedules():
        last_date = get_datetime_from_now(days=0, minutes=2)
        distressed_schedules = (
            Models.Run.objects.filter(
                status=V1Statuses.RUNNING,
                kind=V1RunKind.SCHEDULE,
            )
            .exclude(
                pipeline_runs__finished_at__gte=last_date,
            )
            .annotate(
                unfinished=Count(
                    "pipeline_runs",
                    filter=~Q(pipeline_runs__status__in=LifeCycle.DONE_VALUES),
                    distinct=True,
                ),
            )
            .filter(
                unfinished=0,
            )
            .values_list("id", flat=True)
        )
        for _id in distressed_schedules:
            workers.send(
                SchedulerCeleryTasks.RUNS_WAKEUP_SCHEDULE,
                kwargs={"run_id": _id},
            )

    @staticmethod
    def heartbeat_stopping_runs(minutes: int = 30):
        last_date = get_datetime_from_now(days=0, minutes=minutes)
        condition = V1StatusCondition.get_condition(
            type=V1Statuses.STOPPED,
            status="True",
            reason="HeartbeatStopping",
            message="Run is stopped by heartbeat process.",
        )

        # Finish all runs
        runs = Models.Run.objects.filter(
            status=V1Statuses.STOPPING,
            updated_at__lte=last_date,
            kind__in=[
                V1RunKind.JOB,
                V1RunKind.SERVICE,
                V1RunKind.TUNER,
                V1RunKind.NOTIFIER,
            ],
        )
        bulk_new_run_status(runs, condition)

        # Finish all stopping pipelines
        runs = get_stopping_pipelines_with_no_runs(
            Models.Run.objects.filter(updated_at__lte=last_date)
        )
        bulk_new_run_status(runs, condition)

    @staticmethod
    def heartbeat_project_last_updated(
        created_threshold: float = 2, updated_threshold: float = 15
    ):
        time_threshold = get_datetime_from_now(days=0, minutes=created_threshold)
        project_threshold = get_datetime_from_now(days=0, seconds=updated_threshold)
        update_project_based_on_last_updated_entities(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
