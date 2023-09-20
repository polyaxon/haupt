from typing import Dict, List, Optional, Set

from django.conf import settings
from django.db.models import Count, Q

from haupt.common.authentication.base import is_normal_user
from haupt.db.abstracts.runs import BaseRun
from haupt.db.defs import Models
from polyaxon.schemas import (
    LifeCycle,
    ManagedBy,
    V1CompiledOperation,
    V1RunKind,
    V1RunPending,
    V1StatusCondition,
    V1Statuses,
)


def add_run_contributors(
    run: Models.Run,
    users: Optional[List[Models.User]] = None,
    user_ids: Optional[List[int]] = None,
):
    if not settings.HAS_ORG_MANAGEMENT:
        return
    if not run:
        return
    _users = [u.id for u in users if is_normal_user(u)] if users else user_ids
    if not _users:
        return

    run.contributors.add(*_users)


def create_run(
    project_id: int,
    user_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    readme: Optional[str] = None,
    tags: List[int] = None,
    raw_content: Optional[str] = None,
    meta_info: Optional[Dict] = None,
    managed_by: Optional[ManagedBy] = ManagedBy.USER,
) -> BaseRun:
    instance = Models.Run.objects.create(
        project_id=project_id,
        user_id=user_id,
        name=name,
        description=description,
        readme=readme,
        tags=tags,
        kind=V1RunKind.JOB,
        managed_by=managed_by,
        raw_content=raw_content,
        meta_info=meta_info,
        status_conditions=[
            V1StatusCondition.get_condition(
                type=V1Statuses.CREATED,
                status="True",
                reason="ModelManager",
                message="Run is created",
            ).to_dict()
        ],
    )
    return instance


def base_approve_run(run: BaseRun):
    pending = run.pending
    if pending:
        new_pending = None
        if (
            (pending == V1RunPending.BUILD and run.status == V1Statuses.CREATED)
            or pending == V1RunPending.UPLOAD
        ) and run.content:
            compiled_operation = V1CompiledOperation.read(
                run.content
            )  # TODO: Use construct
            if compiled_operation.is_approved is False:
                new_pending = V1RunPending.APPROVAL
        run.pending = new_pending
        run.save(update_fields=["pending", "updated_at"])


def get_runs_for(
    run_id: int,
    status: Optional[str],
    statuses: Optional[Set[str]],
    controller: bool = False,
    distinct: bool = True,
):
    filters = {}
    if controller:
        filters["controller_id"] = run_id
    else:
        filters["pipeline_id"] = run_id
    if status:
        filters["status"] = status
    if statuses:
        filters["status__in"] = statuses
    query = Models.Run.objects.filter(**filters)
    if distinct:
        query = query.distinct()

    return query


def is_pipeline_done(run: BaseRun) -> bool:
    return not run.pipeline_runs.exclude(status__in=LifeCycle.DONE_VALUES).exists()


def get_scheduled_runs(run_id: int, controller: bool = False):
    return get_runs_for(
        run_id=run_id, status=V1Statuses.SCHEDULED, statuses=None, controller=controller
    )


def get_succeeded_runs(run_id: int, controller: bool = False):
    return get_runs_for(
        run_id=run_id, status=V1Statuses.SUCCEEDED, statuses=None, controller=controller
    )


def get_failed_runs(run_id: int, controller: bool = False):
    return get_runs_for(
        run_id=run_id, status=V1Statuses.FAILED, statuses=None, controller=controller
    )


def get_stopped_runs(run_id: int, controller: bool = False):
    return get_runs_for(
        run_id=run_id, status=V1Statuses.STOPPED, statuses=None, controller=controller
    )


def get_done_runs(run_id: int, controller: bool = False):
    return get_runs_for(
        run_id=run_id,
        status=None,
        statuses=LifeCycle.DONE_VALUES,
        controller=controller,
    )


def get_pending_runs(run_id: int, controller: bool = False):
    return get_runs_for(
        run_id=run_id,
        status=None,
        statuses=LifeCycle.PENDING_VALUES,
        controller=controller,
    )


def get_running_runs(run_id: int, controller: bool = False):
    return get_runs_for(
        run_id=run_id,
        status=None,
        statuses=LifeCycle.RUNNING_VALUES,
        controller=controller,
    )


def get_on_k8s_runs(run_id: int, controller: bool = False):
    return get_runs_for(
        run_id=run_id,
        status=None,
        statuses=LifeCycle.ON_K8S_VALUES,
        controller=controller,
    )


def get_failed_stopped_and_all_runs(run_id: int, controller: bool = False):
    query = get_runs_for(
        run_id=run_id,
        status=None,
        statuses=None,
        controller=controller,
        distinct=False,
    )
    return query.aggregate(
        all=Count(
            "id",
            distinct=True,
        ),
        failed=Count(
            "id",
            filter=Q(status=V1Statuses.FAILED),
            distinct=True,
        ),
        stopped=Count(
            "id",
            filter=Q(status=V1Statuses.STOPPED),
            distinct=True,
        ),
    )


def get_stopping_pipelines_with_no_runs(queryset):
    return (
        queryset.filter(
            kind__in=[V1RunKind.DAG, V1RunKind.MATRIX, V1RunKind.SCHEDULE],
            status=V1Statuses.STOPPING,
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
        .filter(unfinished=0)
    )
