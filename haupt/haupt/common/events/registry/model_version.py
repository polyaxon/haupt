from haupt.common.events import event_actions, event_subjects
from haupt.common.events.event import ActorEvent, Attribute

MODEL_VERSION_DELETED = "{}.{}".format(
    event_subjects.MODEL_VERSION, event_actions.DELETED
)
MODEL_VERSION_CREATED_ACTOR = "{}.{}.{}".format(
    event_subjects.MODEL_VERSION, event_actions.CREATED, event_subjects.ACTOR
)
MODEL_VERSION_UPDATED_ACTOR = "{}.{}.{}".format(
    event_subjects.MODEL_VERSION, event_actions.UPDATED, event_subjects.ACTOR
)
MODEL_VERSION_DELETED_ACTOR = "{}.{}.{}".format(
    event_subjects.MODEL_VERSION, event_actions.DELETED, event_subjects.ACTOR
)
MODEL_VERSION_VIEWED_ACTOR = "{}.{}.{}".format(
    event_subjects.MODEL_VERSION, event_actions.VIEWED, event_subjects.ACTOR
)
MODEL_VERSION_TRANSFERRED_ACTOR = "{}.{}.{}".format(
    event_subjects.MODEL_VERSION, event_actions.TRANSFERRED, event_subjects.ACTOR
)
MODEL_VERSION_NEW_STAGE = "{}.{}".format(
    event_subjects.MODEL_VERSION, event_actions.NEW_STAGE
)

EVENTS = {
    MODEL_VERSION_DELETED,
    MODEL_VERSION_CREATED_ACTOR,
    MODEL_VERSION_UPDATED_ACTOR,
    MODEL_VERSION_VIEWED_ACTOR,
    MODEL_VERSION_DELETED_ACTOR,
    MODEL_VERSION_TRANSFERRED_ACTOR,
    MODEL_VERSION_NEW_STAGE,
}

MODEL_VERSION_ATTRIBUTES = (
    Attribute("uuid", is_uuid=True),
    Attribute("name", is_required=False),
    Attribute("owner_id"),
    Attribute("project.uuid", is_uuid=True),
    Attribute("project.name"),
    Attribute("project.owner.name"),
)


class VersionActorEvent(ActorEvent):
    entity_uuid = "project.uuid"


class ModelVersionDeletedEvent(VersionActorEvent):
    event_type = MODEL_VERSION_DELETED
    attributes = (Attribute("id"),)


class ModelVersionCreatedActorEvent(VersionActorEvent):
    event_type = MODEL_VERSION_CREATED_ACTOR
    attributes = MODEL_VERSION_ATTRIBUTES


class ModelVersionUpdatedActorEvent(VersionActorEvent):
    event_type = MODEL_VERSION_UPDATED_ACTOR
    attributes = MODEL_VERSION_ATTRIBUTES


class ModelVersionDeletedActorEvent(VersionActorEvent):
    event_type = MODEL_VERSION_DELETED_ACTOR
    attributes = MODEL_VERSION_ATTRIBUTES


class ModelVersionViewedActorEvent(VersionActorEvent):
    event_type = MODEL_VERSION_VIEWED_ACTOR
    attributes = MODEL_VERSION_ATTRIBUTES


class ModelVersionTransferredActorEvent(VersionActorEvent):
    event_type = MODEL_VERSION_TRANSFERRED_ACTOR
    attributes = MODEL_VERSION_ATTRIBUTES


class ModelVersionNewStageEvent(VersionActorEvent):
    event_type = MODEL_VERSION_NEW_STAGE
    attributes = MODEL_VERSION_ATTRIBUTES + (
        Attribute("stage"),
        Attribute("previous_stage", is_required=False),
    )
