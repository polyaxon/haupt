from haupt.common.events import event_actions, event_subjects
from haupt.common.events.event import ActorEvent, Attribute

COMPONENT_VERSION_DELETED = "{}.{}".format(
    event_subjects.COMPONENT_VERSION, event_actions.DELETED
)
COMPONENT_VERSION_CREATED_ACTOR = "{}.{}.{}".format(
    event_subjects.COMPONENT_VERSION, event_actions.CREATED, event_subjects.ACTOR
)
COMPONENT_VERSION_UPDATED_ACTOR = "{}.{}.{}".format(
    event_subjects.COMPONENT_VERSION, event_actions.UPDATED, event_subjects.ACTOR
)
COMPONENT_VERSION_DELETED_ACTOR = "{}.{}.{}".format(
    event_subjects.COMPONENT_VERSION, event_actions.DELETED, event_subjects.ACTOR
)
COMPONENT_VERSION_VIEWED_ACTOR = "{}.{}.{}".format(
    event_subjects.COMPONENT_VERSION, event_actions.VIEWED, event_subjects.ACTOR
)
COMPONENT_VERSION_TRANSFERRED_ACTOR = "{}.{}.{}".format(
    event_subjects.COMPONENT_VERSION, event_actions.TRANSFERRED, event_subjects.ACTOR
)
COMPONENT_VERSION_NEW_STAGE = "{}.{}".format(
    event_subjects.COMPONENT_VERSION, event_actions.NEW_STAGE
)

EVENTS = {
    COMPONENT_VERSION_DELETED,
    COMPONENT_VERSION_CREATED_ACTOR,
    COMPONENT_VERSION_UPDATED_ACTOR,
    COMPONENT_VERSION_VIEWED_ACTOR,
    COMPONENT_VERSION_DELETED_ACTOR,
    COMPONENT_VERSION_TRANSFERRED_ACTOR,
    COMPONENT_VERSION_NEW_STAGE,
}

COMPONENT_VERSION_ATTRIBUTES = (
    Attribute("uuid", is_uuid=True),
    Attribute("name", is_required=False),
    Attribute("owner_id"),
    Attribute("project.uuid", is_uuid=True),
    Attribute("project.name"),
    Attribute("project.owner.name"),
)


class VersionActorEvent(ActorEvent):
    entity_uuid = "project.uuid"


class ComponentVersionDeletedEvent(VersionActorEvent):
    event_type = COMPONENT_VERSION_DELETED
    attributes = COMPONENT_VERSION_ATTRIBUTES


class ComponentVersionCreatedActorEvent(VersionActorEvent):
    event_type = COMPONENT_VERSION_CREATED_ACTOR
    attributes = COMPONENT_VERSION_ATTRIBUTES


class ComponentVersionUpdatedActorEvent(VersionActorEvent):
    event_type = COMPONENT_VERSION_UPDATED_ACTOR
    attributes = COMPONENT_VERSION_ATTRIBUTES


class ComponentVersionDeletedActorEvent(VersionActorEvent):
    event_type = COMPONENT_VERSION_DELETED_ACTOR
    attributes = COMPONENT_VERSION_ATTRIBUTES


class ComponentVersionViewedActorEvent(VersionActorEvent):
    event_type = COMPONENT_VERSION_VIEWED_ACTOR
    attributes = COMPONENT_VERSION_ATTRIBUTES


class ComponentVersionTransferredActorEvent(VersionActorEvent):
    event_type = COMPONENT_VERSION_TRANSFERRED_ACTOR
    attributes = COMPONENT_VERSION_ATTRIBUTES


class ComponentVersionNewStageEvent(VersionActorEvent):
    event_type = COMPONENT_VERSION_NEW_STAGE
    attributes = COMPONENT_VERSION_ATTRIBUTES + (
        Attribute("stage"),
        Attribute("previous_stage", is_required=False),
    )
