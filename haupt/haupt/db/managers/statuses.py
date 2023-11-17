from typing import Any, Dict, List, Optional

from clipped.utils.lists import to_list

from haupt.common import auditor
from haupt.common.events.registry.run import (
    RUN_DONE,
    RUN_FAILED,
    RUN_NEW_STATUS,
    RUN_RESUMED,
    RUN_SKIPPED,
    RUN_STOPPED,
    RUN_SUCCEEDED,
)
from haupt.db.abstracts.runs import BaseRun
from haupt.db.defs import Models
from polyaxon.schemas import LifeCycle, V1StatusCondition, V1Statuses


def get_run_conditions(entity) -> List[V1StatusCondition]:
    if entity.status_conditions:
        status_conditions = to_list(entity.status_conditions, check_none=True)
    else:
        status_conditions = []
    return [V1StatusCondition.get_condition(**c) for c in status_conditions]


def sort_conditions(status_conditions):
    return sorted(
        status_conditions,
        key=lambda x: V1StatusCondition.get_last_update_time(
            x.get("last_transition_time")
        ),
    )


def set_entity_status(entity, condition: V1StatusCondition):
    entity.status = condition.type

    if condition:
        status_conditions = None
        if entity.status_conditions:
            status_conditions = to_list(entity.status_conditions, check_none=True)
            last_condition = V1StatusCondition.get_condition(**status_conditions[-1])
            if last_condition == condition:
                status_conditions[-1] = condition.to_dict()
            else:
                status_conditions.append(condition.to_dict())
        elif condition:
            status_conditions = [condition.to_dict()]
        if status_conditions:
            entity.status_conditions = status_conditions

    return entity


def new_status(
    entity,
    condition: V1StatusCondition,
    additional_fields: Optional[List[str]] = None,
    force: bool = False,
):
    previous_status = entity.status
    if condition.type == V1Statuses.CREATED:
        return previous_status
    if previous_status == V1Statuses.STOPPING and not LifeCycle.is_done(condition.type):
        return previous_status
    # Do not override final status
    if LifeCycle.is_done(previous_status) and not force:
        return previous_status

    entity = set_entity_status(entity=entity, condition=condition)

    LifeCycle.set_started_at(entity=entity)
    LifeCycle.set_finished_at(entity=entity)
    additional_fields = additional_fields or []
    entity.save(
        update_fields=additional_fields
        + [
            "status_conditions",
            "status",
            "started_at",
            "updated_at",
            "finished_at",
            "wait_time",
            "duration",
        ]
    )

    return previous_status


def bulk_new_entity_status(
    model_class,
    entities: List[Any],
    condition: V1StatusCondition,
    additional_fields: Optional[List[str]] = None,
):
    for entity in entities:
        set_entity_status(entity=entity, condition=condition)
    additional_fields = additional_fields or []
    model_class.all.bulk_update(
        entities, additional_fields + ["status_conditions", "status"]
    )


def bulk_new_run_status(
    runs: List[BaseRun],
    condition: V1StatusCondition,
    additional_fields: Optional[List[str]] = None,
):
    bulk_new_entity_status(
        model_class=Models.Run,
        entities=runs,
        condition=condition,
        additional_fields=additional_fields,
    )


def new_run_status(
    run: BaseRun,
    condition: V1StatusCondition,
    additional_fields: Optional[List[str]] = None,
    force: bool = False,
):
    previous_status = new_status(
        entity=run,
        condition=condition,
        additional_fields=additional_fields,
        force=force,
    )
    # Do not audit the new status since it's the same as the previous one
    if (
        condition.type in {V1Statuses.CREATED, V1Statuses.STOPPING}
        or previous_status == run.status
    ):
        return

    auditor.record(
        event_type=RUN_NEW_STATUS, instance=run, previous_status=previous_status
    )
    if run.status == V1Statuses.STOPPED:
        auditor.record(
            event_type=RUN_STOPPED, instance=run, previous_status=previous_status
        )
    elif run.status == V1Statuses.FAILED:
        auditor.record(
            event_type=RUN_FAILED, instance=run, previous_status=previous_status
        )
    elif run.status == V1Statuses.SUCCEEDED:
        auditor.record(
            event_type=RUN_SUCCEEDED, instance=run, previous_status=previous_status
        )
    elif run.status == V1Statuses.SKIPPED:
        auditor.record(
            event_type=RUN_SKIPPED, instance=run, previous_status=previous_status
        )
    elif run.status == V1Statuses.RESUMING:
        auditor.record(event_type=RUN_RESUMED, instance=run)

    # handle done status
    if LifeCycle.is_done(run.status):
        auditor.record(
            event_type=RUN_DONE, instance=run, previous_status=previous_status
        )


def new_run_stop_status(
    run: Models.Run, message: str, meta_info: Optional[Dict] = None
):
    # Update run status to show that its stopped
    message = f"Run is stopped; {message}" if message else "Run is stopped"
    condition = V1StatusCondition.get_condition(
        type=V1Statuses.STOPPED,
        status="True",
        reason="StateManager",
        message=message,
        meta_info=meta_info,
    )
    new_run_status(run=run, condition=condition)


def new_run_stopping_status(
    run: Models.Run, message: str, meta_info: Optional[Dict] = None
) -> bool:
    if LifeCycle.is_done(run.status, progressing=True):
        return False

    if LifeCycle.is_safe_stoppable(run.status):
        new_run_stop_status(run, message, meta_info=meta_info)
        return True
    message = f"Run is stopping; {message}" if message else "Run is stopping"
    condition = V1StatusCondition.get_condition(
        type=V1Statuses.STOPPING,
        status="True",
        reason="StateManager",
        message=message,
        meta_info=meta_info,
    )
    new_run_status(run=run, condition=condition)
    return True


def new_run_skip_status(
    run: Models.Run, message: str, meta_info: Optional[Dict] = None
):
    # Update run status to show that its stopped
    message = f"Run is skipped; {message}" if message else "Run is skipped"
    condition = V1StatusCondition.get_condition(
        type=V1Statuses.SKIPPED,
        status="True",
        reason="StateManager",
        message=message,
        meta_info=meta_info,
    )
    new_run_status(run=run, condition=condition)


def new_run_skipped_status(
    run: Models.Run, message: str, meta_info: Optional[Dict] = None
) -> bool:
    if LifeCycle.is_done(run.status, progressing=True):
        return False

    if not LifeCycle.is_safe_stoppable(run.status):
        return False
    new_run_skip_status(run, message, meta_info)
    return True
