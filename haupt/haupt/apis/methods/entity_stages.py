from typing import Optional

from django.conf import settings

from haupt.common.authentication.base import is_normal_user
from haupt.db.managers.stages import new_stage
from haupt.db.managers.versions import add_version_contributors
from polyaxon.schemas import V1StageCondition


def create_stage(view, serializer, event_type: Optional[str] = None):
    serializer.is_valid()
    validated_data = serializer.validated_data
    if not validated_data:
        return
    condition = None
    if validated_data.get("condition"):
        condition = V1StageCondition.get_condition(**validated_data.get("condition"))
    if not condition:
        return
    if settings.HAS_ORG_MANAGEMENT and is_normal_user(view.request.user):
        status_meta_info = {
            "user": {
                "username": view.request.user.username,
                "email": view.request.user.email,
            },
        }
        condition.meta_info = status_meta_info
    new_stage(
        entity=view.version,
        owner_id=view._owner_id,
        user=view.request.user,
        condition=condition,
        event_type=event_type,
    )
    add_version_contributors(view.version, users=[view.request.user])
