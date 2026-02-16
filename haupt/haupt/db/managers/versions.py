import uuid

from typing import List, Optional

from django.conf import settings

from haupt.common import auditor
from haupt.common.authentication.base import is_normal_user
from haupt.common.events.registry.artifact_version import (
    ARTIFACT_VERSION_TRANSFERRED_ACTOR,
)
from haupt.common.events.registry.component_version import (
    COMPONENT_VERSION_TRANSFERRED_ACTOR,
)
from haupt.common.events.registry.model_version import (
    MODEL_VERSION_TRANSFERRED_ACTOR,
)
from haupt.db.abstracts.projects import Owner
from haupt.db.defs import Models
from polyaxon.pkg import SCHEMA_VERSION
from polyaxon.schemas import V1Component, V1ProjectVersionKind

VERSION_TRANSFER_EVENTS = {
    V1ProjectVersionKind.MODEL: MODEL_VERSION_TRANSFERRED_ACTOR,
    V1ProjectVersionKind.ARTIFACT: ARTIFACT_VERSION_TRANSFERRED_ACTOR,
    V1ProjectVersionKind.COMPONENT: COMPONENT_VERSION_TRANSFERRED_ACTOR,
}


def add_version_contributors(
    version: Models.ProjectVersion,
    users: Optional[List[Models.User]] = None,
    user_ids: Optional[List[int]] = None,
):
    if not settings.HAS_ORG_MANAGEMENT:
        return
    if not version:
        return
    _users = [u.id for u in users if is_normal_user(u)] if users else user_ids
    if not _users:
        return

    version.contributors.add(*_users)


def get_component_version_state(
    component: V1Component,
) -> Optional[uuid.UUID]:
    """A string representation that is used to create hash version"""
    component.kind = "component"
    component.version = SCHEMA_VERSION
    return uuid.uuid5(Owner.uuid, component.to_json())


def transfer_version_action(
    version: Models.ProjectVersion,
    dest_project: Models.Project,
    contributor_user: Optional[Models.User] = None,
    audit=False,
) -> bool:
    if version.project_id == dest_project.id:
        return False
    version.project_id = dest_project.id
    version.save(update_fields=["project_id", "updated_at"])
    if contributor_user:
        add_version_contributors(version, users=[contributor_user])
    if audit:
        event_type = VERSION_TRANSFER_EVENTS.get(version.kind)
        if event_type:
            auditor.record(event_type=event_type, instance=version)
    return True
