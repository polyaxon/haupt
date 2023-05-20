from typing import Optional

from haupt.db.managers.stages import new_stage
from polyaxon.lifecycle import V1StageCondition


def create_stage(view, serializer, event_type: Optional[str] = None):
    serializer.is_valid()
    validated_data = serializer.validated_data
    if not validated_data:
        return
    condition = None
    if validated_data.get("condition"):
        condition = V1StageCondition.get_condition(**validated_data.get("condition"))
    if condition:
        new_stage(
            entity=view.version,
            owner_id=view._owner_id,
            user=view.request.user,
            condition=condition,
            event_type=event_type,
        )
