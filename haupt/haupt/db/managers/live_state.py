from typing import List

from django.conf import settings
from django.db.models import Q, QuerySet
from django.utils.timezone import now

from haupt.db.abstracts.runs import BaseRun
from haupt.db.defs import Models
from polyaxon.schemas import LifeCycle, LiveState, V1Statuses


def run_queryset_stopping(queryset):
    queryset.exclude(status__in=LifeCycle.DONE_OR_IN_PROGRESS_VALUES).update(
        status=V1Statuses.STOPPING
    )


def delete_in_progress_project(project: Models.Project):
    if not project.delete_in_progress(update_name=True):
        return False
    Models.Run.all.filter(project=project).exclude(
        live_state=LiveState.DELETION_PROGRESSING
    ).update(live_state=LiveState.DELETION_PROGRESSING)
    # Delete right away
    if settings.HAS_ORG_MANAGEMENT:
        confirm_delete_runs(
            runs=Models.Run.all.filter(project=project, agent__isnull=True)
        )

    return True


def delete_in_progress_run(run: BaseRun):
    if not run.delete_in_progress(set_deleted_at=False):
        return False
    Models.Run.all.filter(Q(pipeline=run) | Q(controller=run)).exclude(
        live_state=LiveState.DELETION_PROGRESSING
    ).update(live_state=LiveState.DELETION_PROGRESSING)
    # Delete right away
    if settings.HAS_ORG_MANAGEMENT:
        confirm_delete_runs(
            runs=Models.Run.all.filter(pipeline=run, agent__isnull=True)
        )
    return True


def archive_project(project: Models.Project):
    if not project.archive():
        return False
    queryset = Models.Run.objects.filter(project=project).exclude(
        live_state=LiveState.ARCHIVED
    )
    run_queryset_stopping(queryset=queryset)
    queryset.update(live_state=LiveState.ARCHIVED, archived_at=now())
    return True


def archive_run(run: BaseRun):
    if not run.archive(commit=False):
        return False
    if not LifeCycle.is_done(run.status, progressing=True):
        run.status = V1Statuses.STOPPING
    run.save(update_fields=["live_state", "status", "archived_at", "updated_at"])
    queryset = Models.Run.objects.filter(
        Q(pipeline_id=run.id) | Q(controller_id=run.id)
    ).exclude(live_state=LiveState.ARCHIVED)
    run_queryset_stopping(queryset=queryset)
    queryset.update(live_state=LiveState.ARCHIVED, archived_at=now())
    return True


def confirm_delete_run(run: BaseRun):
    if not run.confirm_delete():
        return False
    queryset = Models.Run.all.filter(
        Q(pipeline_id=run.id) | Q(controller_id=run.id)
    ).exclude(live_state=LiveState.DELETION_PROGRESSING, deleted_at__isnull=False)
    run_queryset_stopping(queryset=queryset)
    queryset.update(live_state=LiveState.DELETION_PROGRESSING, deleted_at=now())
    return True


def confirm_delete_runs(runs: QuerySet, run_ids: List[int] = None):
    run_ids = run_ids or list(runs.values_list("id", flat=True))
    if not run_ids:
        return
    runs.update(live_state=LiveState.DELETION_PROGRESSING, deleted_at=now())
    Models.Run.all.filter(id__in=run_ids).exclude(
        status__in=LifeCycle.DONE_VALUES
    ).update(status=V1Statuses.STOPPED)
    queryset = Models.Run.all.filter(
        Q(pipeline_id__in=run_ids) | Q(controller_id__in=run_ids)
    ).exclude(live_state=LiveState.DELETION_PROGRESSING, deleted_at__isnull=False)
    run_queryset_stopping(queryset=queryset)
    queryset.update(live_state=LiveState.DELETION_PROGRESSING, deleted_at=now())


def restore_project(project: Models.Project):
    if not project.restore():
        return False
    Models.Run.archived.filter(project=project).update(
        live_state=LiveState.LIVE, archived_at=None, deleted_at=None
    )
    return True


def restore_run(run: BaseRun):
    if not run.restore():
        return False
    Models.Run.archived.filter(pipeline=run).update(
        live_state=LiveState.LIVE, archived_at=None, deleted_at=None
    )
    return True
