from django.conf import settings
from django.db.models import Q

from haupt.db.abstracts.projects import BaseProject
from haupt.db.abstracts.runs import BaseRun
from haupt.db.defs import Models
from polyaxon.lifecycle import LifeCycle, LiveState, V1Statuses


def run_queryset_stopping(queryset):
    queryset.exclude(status__in=LifeCycle.DONE_OR_IN_PROGRESS_VALUES).update(
        status=V1Statuses.STOPPING
    )


def delete_in_progress_project(project: BaseProject):
    if not project.delete_in_progress(update_name=True):
        return False
    Models.Run.all.filter(project=project).exclude(
        live_state=LiveState.DELETION_PROGRESSING
    ).update(live_state=LiveState.DELETION_PROGRESSING)
    # Delete right away
    if settings.HAS_ORG_MANAGEMENT:
        Models.Run.all.filter(project=project, agent__isnull=True).delete()

    return True


def delete_in_progress_run(run: BaseRun):
    if not run.delete_in_progress():
        return False
    Models.Run.all.filter(Q(pipeline=run) | Q(controller=run)).exclude(
        live_state=LiveState.DELETION_PROGRESSING
    ).update(live_state=LiveState.DELETION_PROGRESSING)
    # Delete right away
    if settings.HAS_ORG_MANAGEMENT:
        Models.Run.all.filter(pipeline=run, agent__isnull=True).delete()
    return True


def archive_project(project: BaseProject):
    if not project.archive():
        return False
    queryset = Models.Run.objects.filter(project=project).exclude(
        live_state=LiveState.ARCHIVED
    )
    run_queryset_stopping(queryset=queryset)
    queryset.update(live_state=LiveState.ARCHIVED)
    return True


def archive_run(run: BaseRun):
    if not run.archive(commit=False):
        return False
    if not LifeCycle.is_done(run.status, progressing=True):
        run.status = V1Statuses.STOPPING
    run.save(update_fields=["live_state", "status"])
    queryset = Models.Run.objects.filter(
        Q(pipeline_id=run.id) | Q(controller_id=run.id)
    ).exclude(live_state=LiveState.ARCHIVED)
    run_queryset_stopping(queryset=queryset)
    queryset.update(live_state=LiveState.ARCHIVED)
    return True


def restore_project(project: BaseProject):
    if not project.restore():
        return False
    Models.Run.archived.filter(project=project).update(live_state=LiveState.LIVE)
    return True


def restore_run(run: BaseRun):
    if not run.restore():
        return False
    Models.Run.archived.filter(pipeline=run).update(live_state=LiveState.LIVE)
    return True
