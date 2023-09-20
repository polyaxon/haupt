import uuid

from typing import List, Optional

from django.conf import settings

from haupt.common.authentication.base import is_normal_user
from haupt.db.abstracts.projects import Owner
from haupt.db.defs import Models
from polyaxon.pkg import SCHEMA_VERSION
from polyaxon.schemas import V1Component


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
