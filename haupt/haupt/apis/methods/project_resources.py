#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from rest_framework import status
from rest_framework.response import Response

from haupt.apis.serializers.base.tags import TagsMixin
from haupt.common import auditor
from haupt.common.events.registry.run import (
    RUN_APPROVED_ACTOR,
    RUN_DELETED_ACTOR,
    RUN_STOPPED_ACTOR,
)
from haupt.db.abstracts.getter import get_run_model
from haupt.db.managers.statuses import bulk_new_run_status
from polyaxon import live_state
from polyaxon.lifecycle import LifeCycle, V1StatusCondition, V1Statuses
from polyaxon.schemas import V1RunPending


def create_runs_tags(view, request, *args, **kwargs):
    uuids = request.data.get("uuids", [])
    tags = request.data.get("tags", [])
    if not tags:
        return Response(status=status.HTTP_200_OK, data={})

    updated = []
    run_model = get_run_model()
    queryset = view.enrich_queryset(run_model.all)
    queryset = queryset.filter(uuid__in=uuids)
    for run in queryset.only("id", "tags"):
        run.tags = TagsMixin.validated_tags({"tags": tags, "merge": True}, run.tags)[
            "tags"
        ]
        updated.append(run)

        run_model.objects.bulk_update(updated, ["tags"])
    return Response(status=status.HTTP_200_OK, data={})


def stop_runs(view, request, actor, *args, **kwargs):
    uuids = request.data.get("uuids", [])
    # Immediate stop
    queryset = view.enrich_queryset(get_run_model().restorable)
    queryset = queryset.filter(uuid__in=uuids)
    queryset = queryset.filter(status__in=LifeCycle.SAFE_STOP_VALUES)
    condition = V1StatusCondition.get_condition(
        type=V1Statuses.STOPPED,
        status="True",
        reason="EventHandler",
        message="User requested to stop the run.",
    )
    bulk_new_run_status(queryset, condition)

    queryset = view.enrich_queryset(get_run_model().restorable)
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
    queryset = view.enrich_queryset(get_run_model().objects)
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
    queryset = view.enrich_queryset(get_run_model().restorable)
    runs = queryset.filter(uuid__in=uuids)
    # Delete non managed immediately
    runs.filter(is_managed=False).delete()
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
    runs.filter(is_managed=True).update(
        live_state=live_state.STATE_DELETION_PROGRESSING
    )
    return Response(status=status.HTTP_200_OK, data={})
