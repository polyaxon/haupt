from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from django.conf import settings

from haupt.apis.serializers.base.tags import TagsMixin
from haupt.common import auditor
from haupt.common.content_types import ContentTypes
from haupt.common.events.registry.archive import RUN_ARCHIVED_ACTOR, RUN_RESTORED_ACTOR
from haupt.common.events.registry.run import (
    RUN_APPROVED_ACTOR,
    RUN_DELETED_ACTOR,
    RUN_STOPPED_ACTOR,
    RUN_TRANSFERRED_ACTOR,
)
from haupt.db.defs import Models
from haupt.db.managers.bookmarks import bookmark_obj
from haupt.db.managers.statuses import bulk_new_run_status
from polyaxon.lifecycle import LifeCycle, LiveState, V1StatusCondition, V1Statuses
from polyaxon.schemas import V1RunPending


def create_runs_tags(view, request, *args, **kwargs):
    uuids = request.data.get("uuids", [])
    tags = request.data.get("tags", [])
    if not tags:
        return Response(status=status.HTTP_200_OK, data={})

    updated = []
    queryset = view.enrich_queryset(Models.Run.all)
    queryset = queryset.filter(uuid__in=uuids)
    for run in queryset.only("id", "tags"):
        run.tags = TagsMixin.validated_tags({"tags": tags, "merge": True}, run.tags)[
            "tags"
        ]
        updated.append(run)

        Models.Run.objects.bulk_update(updated, ["tags"])
    return Response(status=status.HTTP_200_OK, data={})


def stop_runs(view, request, actor, *args, **kwargs):
    uuids = request.data.get("uuids", [])
    # Immediate stop
    queryset = view.enrich_queryset(Models.Run.restorable)
    queryset = queryset.filter(uuid__in=uuids)
    queryset = queryset.filter(status__in=LifeCycle.SAFE_STOP_VALUES)
    condition = V1StatusCondition.get_condition(
        type=V1Statuses.STOPPED,
        status="True",
        reason="EventHandler",
        message="User requested to stop the run.",
    )
    bulk_new_run_status(queryset, condition)

    queryset = view.enrich_queryset(Models.Run.restorable)
    queryset = queryset.filter(uuid__in=uuids)
    queryset = queryset.exclude(status__in=LifeCycle.DONE_OR_IN_PROGRESS_VALUES)
    runs = [r for r in queryset]
    condition = V1StatusCondition.get_condition(
        type=V1Statuses.STOPPING,
        status="True",
        reason="EventHandler",
        message="User requested to stop the run.",
    )
    bulk_new_run_status(runs, condition)
    # For Audit
    view.set_owner()
    for run in runs:
        auditor.record(
            event_type=RUN_STOPPED_ACTOR,
            instance=run,
            actor_id=actor.id,
            actor_name=actor.username,
            owner_id=view._owner_id,
            owner_name=view.owner_name,
            project_name=view.project_name,
        )

    return Response(status=status.HTTP_200_OK, data={})


def approve_runs(view, request, actor, *args, **kwargs):
    uuids = request.data.get("uuids", [])
    queryset = view.enrich_queryset(Models.Run.objects)
    queryset = queryset.filter(uuid__in=uuids)
    queryset = queryset.filter(
        pending__in={V1RunPending.APPROVAL, V1RunPending.CACHE},
    )
    runs = [r for r in queryset]
    queryset.update(pending=None)
    # For Audit
    view.set_owner()
    for run in runs:
        auditor.record(
            event_type=RUN_APPROVED_ACTOR,
            instance=run,
            actor_id=actor.id,
            actor_name=actor.username,
            owner_id=view._owner_id,
            owner_name=view.owner_name,
            project_name=view.project_name,
        )

    return Response(status=status.HTTP_200_OK, data={})


def delete_runs(view, request, actor, *args, **kwargs):
    uuids = request.data.get("uuids", [])
    queryset = view.enrich_queryset(Models.Run.restorable)
    runs = queryset.filter(uuid__in=uuids)
    # For Audit
    view.set_owner()
    for run in runs:
        auditor.record(
            event_type=RUN_DELETED_ACTOR,
            instance=run,
            actor_id=actor.id,
            actor_name=actor.username,
            owner_id=view._owner_id,
            owner_name=view.owner_name,
            project_name=view.project_name,
        )
    # Deletion in progress
    runs.update(live_state=LiveState.DELETION_PROGRESSING)
    return Response(status=status.HTTP_200_OK, data={})


def invalidate_runs(view, request, actor, *args, **kwargs):
    uuids = request.data.get("uuids", [])
    queryset = view.enrich_queryset(Models.Run.all)
    queryset.filter(uuid__in=uuids).update(state=None)
    return Response(status=status.HTTP_200_OK, data={})


def archive_runs(view, request, actor, *args, **kwargs):
    uuids = request.data.get("uuids", [])
    queryset = view.enrich_queryset(Models.Run.objects)
    queryset = queryset.filter(uuid__in=uuids)
    # Set to stopping all runs that are not ended yet
    queryset.exclude(status__in=LifeCycle.DONE_OR_IN_PROGRESS_VALUES).update(
        status=V1Statuses.STOPPING,
    )
    # Pipeline runs
    Models.Run.objects.filter(pipeline__uuid__in=uuids).update(
        live_state=LiveState.ARCHIVED
    )
    runs = [r for r in queryset]
    queryset.update(live_state=LiveState.ARCHIVED)
    # For Audit
    view.set_owner()
    for run in runs:
        auditor.record(
            event_type=RUN_ARCHIVED_ACTOR,
            instance=run,
            actor_id=actor.id,
            actor_name=actor.username,
            owner_id=view._owner_id,
            owner_name=view.owner_name,
            project_name=view.project_name,
        )

    return Response(status=status.HTTP_200_OK, data={})


def restore_runs(view, request, actor, *args, **kwargs):
    uuids = request.data.get("uuids", [])
    queryset = view.enrich_queryset(Models.Run.archived)
    queryset = queryset.filter(uuid__in=uuids)
    # Restore pipeline runs
    Models.Run.archived.filter(pipeline__uuid__in=uuids).update(
        live_state=LiveState.LIVE
    )
    runs = [r for r in queryset]
    queryset.update(live_state=LiveState.LIVE)
    # For Audit
    view.set_owner()
    for run in runs:
        auditor.record(
            event_type=RUN_RESTORED_ACTOR,
            instance=run,
            actor_id=actor.id,
            actor_name=actor.username,
            owner_id=view._owner_id,
            owner_name=view.owner_name,
            project_name=view.project_name,
        )

    return Response(status=status.HTTP_200_OK, data={})


def bookmarks_runs(view, request, actor, *args, **kwargs):
    uuids = request.data.get("uuids", [])
    user = request.user if settings.HAS_ORG_MANAGEMENT else None
    content_type = ContentTypes.RUN.value
    queryset = view.enrich_queryset(Models.Run.all)
    for run in queryset.filter(uuid__in=uuids).only("id"):
        bookmark_obj(user=user, obj=run, content_type=content_type)

    return Response(status=status.HTTP_200_OK, data={})


def transfer_runs(view, request, actor, *args, **kwargs):
    uuids = request.data.get("uuids", [])
    project_name = request.data.get("project")
    if project_name == view.project_name:
        return Response(status=status.HTTP_200_OK, data={})
    if not project_name:
        raise ValidationError("The destination project was not provided.")
    try:
        filters = {"name": project_name}
        if settings.HAS_ORG_MANAGEMENT:
            filters["owner__name"] = view.owner_name
        dest_project = Models.Project.objects.only("id").get(**filters)
    except Models.Project.DoesNotExist:
        raise ValidationError(
            "The destination project `{}` does not exist.".format(project_name)
        )

    queryset = view.enrich_queryset(Models.Run.all)
    queryset = queryset.filter(uuid__in=uuids)
    run_ids = [i for i in queryset.values_list("id", flat=True)]
    queryset.update(project_id=dest_project.id)
    # For Audit
    view.set_owner()
    for run in Models.Run.all.filter(id__in=run_ids):
        auditor.record(
            event_type=RUN_TRANSFERRED_ACTOR,
            instance=run,
            actor_id=actor.id,
            actor_name=actor.username,
            owner_id=view._owner_id,
            owner_name=view.owner_name,
            project_name=view.project_name,
        )
    return Response(status=status.HTTP_200_OK, data={})
