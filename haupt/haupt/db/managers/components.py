import uuid

from typing import Optional

from haupt.db.abstracts.projects import Owner
from polyaxon.pkg import SCHEMA_VERSION
from polyaxon.polyflow import V1Component


def get_component_version_state(
    component: V1Component,
) -> Optional[uuid.UUID]:
    """A string representation that is used to create hash version"""
    component.kind = "component"
    component.version = SCHEMA_VERSION
    return uuid.uuid5(Owner.uuid, component.to_json())
