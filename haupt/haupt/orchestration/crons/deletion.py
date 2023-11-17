from clipped.utils.tz import get_datetime_from_now

from django.conf import settings
from django.db.models import Count, Q

from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.common import conf, workers
from haupt.common.options.registry.cleaning import (
    CLEANING_INTERVALS_ARCHIVES,
    CLEANING_INTERVALS_DELETION,
)
from haupt.db.defs import Models
from haupt.db.managers.live_state import confirm_delete_runs
from polyaxon.schemas import LifeCycle, LiveState, V1RunKind, V1Statuses


class CronsDeletionManager:
    @staticmethod
    def delete_archived_projects():
        last_date = get_datetime_from_now(days=conf.get(CLEANING_INTERVALS_ARCHIVES))
        ids = Models.Project.archived.filter(archived_at__lte=last_date).values_list(
            "id", flat=True
        )
        for _id in ids:
            workers.send(
                SchedulerCeleryTasks.DELETE_ARCHIVED_PROJECT,
                kwargs={"project_id": _id},
            )

    @staticmethod
    def delete_in_progress_projects():
        last_date = get_datetime_from_now(days=conf.get(CLEANING_INTERVALS_DELETION))
        Models.Project.all.filter(
            live_state=LiveState.DELETION_PROGRESSING, deleted_at__lte=last_date
        ).delete()

    @staticmethod
    def delete_in_progress_runs():
        # Delete pipelines without managed runs
        runs = (
            Models.Run.all.filter(
                kind__in={V1RunKind.DAG, V1RunKind.MATRIX, V1RunKind.SCHEDULE},
                live_state=LiveState.DELETION_PROGRESSING,
            )
            .annotate(
                unfinished=Count(
                    "pipeline_runs",
                    filter=~Q(
                        pipeline_runs__status__in=LifeCycle.DONE_VALUES
                        | LifeCycle.PENDING_VALUES
                    ),
                    distinct=True,
                )
            )
            .filter(unfinished=0, deleted_at__isnull=True)
        )
        confirm_delete_runs(runs=runs)

        if settings.HAS_ORG_MANAGEMENT:
            # Delete runs that are not assigned to an agent
            runs = Models.Run.all.filter(
                kind__in={
                    V1RunKind.JOB,
                    V1RunKind.SERVICE,
                    V1RunKind.TUNER,
                    V1RunKind.NOTIFIER,
                },
                live_state=LiveState.DELETION_PROGRESSING,
                agent__isnull=True,
                deleted_at__isnull=True,
            )
            confirm_delete_runs(runs=runs)

        last_date = get_datetime_from_now(days=1)
        Models.Run.all.filter(
            live_state=LiveState.DELETION_PROGRESSING, deleted_at__lte=last_date
        ).delete()

        # Stop all pipelines in deletion progress
        Models.Run.all.filter(
            kind__in={V1RunKind.DAG, V1RunKind.MATRIX, V1RunKind.SCHEDULE},
            live_state=LiveState.DELETION_PROGRESSING,
        ).exclude(status__in=LifeCycle.DONE_VALUES).update(status=V1Statuses.STOPPED)

    @staticmethod
    def delete_archived_runs():
        last_date = get_datetime_from_now(days=conf.get(CLEANING_INTERVALS_ARCHIVES))
        ids = Models.Run.archived.filter(
            # We only check values that will not be deleted by the archived projects
            project__live_state=LiveState.LIVE,
            archived_at__lte=last_date,
        ).values_list("id", flat=True)
        for _id in ids:
            workers.send(
                SchedulerCeleryTasks.DELETE_ARCHIVED_RUN,
                kwargs={"run_id": _id},
            )
