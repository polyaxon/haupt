from typing import List, Optional

from clipped.utils.lists import to_list

from haupt.common import auditor
from polyaxon.schemas import V1StageCondition


def set_entity_stage(entity: str, condition: V1StageCondition) -> str:
    entity.stage = condition.type

    if condition:
        stage_conditions = None
        if entity.stage_conditions:
            stage_conditions = to_list(entity.stage_conditions, check_none=True)
            last_condition = V1StageCondition.get_condition(**stage_conditions[-1])
            if last_condition == condition:
                stage_conditions[-1] = condition.to_dict()
            else:
                stage_conditions.append(condition.to_dict())
        elif condition:
            stage_conditions = [condition.to_dict()]
        if stage_conditions:
            entity.stage_conditions = stage_conditions

    return entity


def new_stage(
    entity: str,
    condition: V1StageCondition,
    additional_fields: Optional[List[str]] = None,
    event_type: Optional[str] = None,
    user=None,
    owner_id: Optional[int] = None,
) -> str:
    previous_stage = entity.stage

    entity = set_entity_stage(entity=entity, condition=condition)

    additional_fields = additional_fields or []
    entity.save(
        update_fields=additional_fields
        + [
            "stage_conditions",
            "stage",
            "updated_at",
        ]
    )

    if event_type and user and owner_id:
        auditor.record(
            event_type=event_type,
            actor_id=user.id,
            actor_name=user.username,
            owner_id=owner_id,
            instance=entity,
            previous_stage=previous_stage,
        )

    return previous_stage
