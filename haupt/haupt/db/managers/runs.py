from typing import Any, Dict, List, Optional, Set

from django.conf import settings
from django.db.models import Count, Q

from haupt.common import auditor
from haupt.common.authentication.base import is_normal_user
from haupt.common.events.registry.archive import (
    RUN_ARCHIVED_ACTOR,
    RUN_RESTORED_ACTOR,
)
from haupt.common.events.registry.run import (
    RUN_INVALIDATED_ACTOR,
    RUN_RESTARTED_ACTOR,
    RUN_RESUMED_ACTOR,
    RUN_SKIPPED_ACTOR,
    RUN_STOPPED_ACTOR,
    RUN_TRANSFERRED_ACTOR,
)
from haupt.db.abstracts.runs import BaseRun
from haupt.db.defs import Models
from haupt.db.managers.live_state import archive_run, restore_run
from haupt.db.managers.statuses import new_run_skipped_status, new_run_stopping_status
from haupt.orchestration import operations
from polyaxon.schemas import (
    LifeCycle,
    ManagedBy,
    V1CloningKind,
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


def stop_run_action(
    run: BaseRun,
    message: str,
    actor_info: Optional[Dict[str, Any]] = None,
    contributor_user: Optional[Models.User] = None,
    audit=False,
) -> bool:
    """
    Stop a run with proper auditing.

    Args:
        run: The run to stop
        message: Reason for stopping
        actor_info: Dict identifying who/what initiated the action
            - {"user": {"username": ..., "email": ...}} for user actions
            - {"automation": {"uuid": ..., "name": ...}} for automation actions
        contributor_user: Optional user to add as contributor

    Returns:
        bool: Whether the stop was successful
    """
    success = new_run_stopping_status(run, message=message, meta_info=actor_info)
    if success:
        if contributor_user:
            add_run_contributors(run, users=[contributor_user])
        if audit:
            auditor.record(event_type=RUN_STOPPED_ACTOR, instance=run)
    return success


def skip_run_action(
    run: BaseRun,
    message: str,
    actor_info: Optional[Dict[str, Any]] = None,
    contributor_user: Optional[Models.User] = None,
    audit=False,
) -> bool:
    """
    Skip a run with proper auditing.

    Args:
        run: The run to skip
        message: Reason for skipping
        actor_info: Dict identifying who/what initiated the action
        contributor_user: Optional user to add as contributor

    Returns:
        bool: Whether the skip was successful
    """
    success = new_run_skipped_status(run, message=message, meta_info=actor_info)
    if success:
        if contributor_user:
            add_run_contributors(run, users=[contributor_user])
        if audit:
            auditor.record(event_type=RUN_SKIPPED_ACTOR, instance=run)
    return success


def restart_run_action(
    run: BaseRun,
    actor_info: Optional[Dict[str, Any]] = None,
    contributor_user: Optional[Models.User] = None,
    audit=False,
    **kwargs,
) -> BaseRun:
    """
    Restart a run with proper auditing.

    Args:
        run: The run to restart
        actor_info: Dict identifying who/what initiated the action
        contributor_user: Optional user to add as contributor
        **kwargs: Passed to operations.restart_run (name, description, content, tags, meta_info)

    Returns:
        The new run instance
    """
    # Handle cache hit runs - restart the original
    if run.cloning_kind == V1CloningKind.CACHE:
        run = run.original

    new_run = operations.restart_run(run=run, **kwargs)
    if contributor_user:
        add_run_contributors(new_run, users=[contributor_user])
    if audit:
        auditor.record(event_type=RUN_RESTARTED_ACTOR, instance=new_run)
    return new_run


def transfer_run_action(
    run: BaseRun,
    dest_project: Models.Project,
    contributor_user: Optional[Models.User] = None,
    audit=False,
) -> bool:
    if run.project_id == dest_project.id:
        return False
    run.project_id = dest_project.id
    run.save(update_fields=["project_id", "updated_at"])
    if run.has_pipeline:
        Models.Run.all.filter(Q(pipeline=run) | Q(controller=run)).update(
            project_id=dest_project.id
        )
    if contributor_user:
        add_run_contributors(run, users=[contributor_user])
    if audit:
        auditor.record(event_type=RUN_TRANSFERRED_ACTOR, instance=run)
    return True


def resume_run_action(
    run: BaseRun,
    actor_info: Optional[Dict[str, Any]] = None,
    contributor_user: Optional[Models.User] = None,
    audit=False,
    **kwargs,
) -> BaseRun:
    """
    Resume a run with proper auditing.

    Args:
        run: The run to resume (must be in a final state)
        actor_info: Dict identifying who/what initiated the action
        contributor_user: Optional user to add as contributor
        **kwargs: Passed to operations.resume_run (name, description, content, tags, meta_info, message)

    Returns:
        The resumed run instance

    Raises:
        ValueError: If run is not in a final state or is a cache hit
    """
    # Validation - must be done
    if not LifeCycle.is_done(run.status):
        raise ValueError(
            f"Cannot resume run, must be in a final state. Current status: {run.status}"
        )

    # Validation - cannot resume cache hits
    if run.cloning_kind == V1CloningKind.CACHE:
        raise ValueError("Cannot resume cache hit runs - they were never executed")

    resumed_run = operations.resume_run(run=run, **kwargs)
    if contributor_user:
        add_run_contributors(resumed_run, users=[contributor_user])
    if audit:
        auditor.record(event_type=RUN_RESUMED_ACTOR, instance=resumed_run)
    return resumed_run


def invalidate_run_action(
    run: BaseRun,
    contributor_user: Optional[Models.User] = None,
    audit=False,
) -> bool:
    run.state = None
    run.save(update_fields=["state"])
    if contributor_user:
        add_run_contributors(run, users=[contributor_user])
    if audit:
        auditor.record(event_type=RUN_INVALIDATED_ACTOR, instance=run)
    return True


def archive_run_action(
    run: BaseRun,
    contributor_user: Optional[Models.User] = None,
    audit=False,
) -> bool:
    success = archive_run(run)
    if success:
        if contributor_user:
            add_run_contributors(run, users=[contributor_user])
        if audit:
            auditor.record(event_type=RUN_ARCHIVED_ACTOR, instance=run)
    return success


def restore_run_action(
    run: BaseRun,
    contributor_user: Optional[Models.User] = None,
    audit=False,
) -> bool:
    success = restore_run(run)
    if success:
        if contributor_user:
            add_run_contributors(run, users=[contributor_user])
        if audit:
            auditor.record(event_type=RUN_RESTORED_ACTOR, instance=run)
    return success
