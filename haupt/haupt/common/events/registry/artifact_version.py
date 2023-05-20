from haupt.common.events import event_actions, event_subjects
from haupt.common.events.event import ActorEvent, Attribute

ARTIFACT_VERSION_DELETED = "{}.{}".format(
    event_subjects.ARTIFACT_VERSION, event_actions.DELETED
)
ARTIFACT_VERSION_CREATED_ACTOR = "{}.{}.{}".format(
    event_subjects.ARTIFACT_VERSION, event_actions.CREATED, event_subjects.ACTOR
)
ARTIFACT_VERSION_UPDATED_ACTOR = "{}.{}.{}".format(
    event_subjects.ARTIFACT_VERSION, event_actions.UPDATED, event_subjects.ACTOR
)
ARTIFACT_VERSION_DELETED_ACTOR = "{}.{}.{}".format(
    event_subjects.ARTIFACT_VERSION, event_actions.DELETED, event_subjects.ACTOR
)
ARTIFACT_VERSION_VIEWED_ACTOR = "{}.{}.{}".format(
    event_subjects.ARTIFACT_VERSION, event_actions.VIEWED, event_subjects.ACTOR
)
ARTIFACT_VERSION_TRANSFERRED_ACTOR = "{}.{}.{}".format(
    event_subjects.ARTIFACT_VERSION, event_actions.TRANSFERRED, event_subjects.ACTOR
)
ARTIFACT_VERSION_NEW_STAGE = "{}.{}".format(
    event_subjects.ARTIFACT_VERSION, event_actions.NEW_STAGE
)

EVENTS = {
    ARTIFACT_VERSION_DELETED,
    ARTIFACT_VERSION_CREATED_ACTOR,
    ARTIFACT_VERSION_UPDATED_ACTOR,
    ARTIFACT_VERSION_VIEWED_ACTOR,
    ARTIFACT_VERSION_DELETED_ACTOR,
    ARTIFACT_VERSION_TRANSFERRED_ACTOR,
    ARTIFACT_VERSION_NEW_STAGE,
}

ARTIFACT_VERSION_ATTRIBUTES = (
    Attribute("uuid", is_uuid=True),
    Attribute("name", is_required=False),
    Attribute("owner_id"),
    Attribute("project.uuid", is_uuid=True),
    Attribute("project.name"),
    Attribute("project.owner.name"),
)


class VersionActorEvent(ActorEvent):
    entity_uuid = "project.uuid"


class ArtifactVersionDeletedEvent(VersionActorEvent):
    event_type = ARTIFACT_VERSION_DELETED
    attributes = (Attribute("id"),)


class ArtifactVersionCreatedActorEvent(VersionActorEvent):
    event_type = ARTIFACT_VERSION_CREATED_ACTOR
    attributes = ARTIFACT_VERSION_ATTRIBUTES


class ArtifactVersionUpdatedActorEvent(VersionActorEvent):
    event_type = ARTIFACT_VERSION_UPDATED_ACTOR
    attributes = ARTIFACT_VERSION_ATTRIBUTES


class ArtifactVersionDeletedActorEvent(VersionActorEvent):
    event_type = ARTIFACT_VERSION_DELETED_ACTOR
    attributes = ARTIFACT_VERSION_ATTRIBUTES


class ArtifactVersionViewedActorEvent(VersionActorEvent):
    event_type = ARTIFACT_VERSION_VIEWED_ACTOR
    attributes = ARTIFACT_VERSION_ATTRIBUTES


class ArtifactVersionTransferredActorEvent(VersionActorEvent):
    event_type = ARTIFACT_VERSION_TRANSFERRED_ACTOR
    attributes = ARTIFACT_VERSION_ATTRIBUTES


class ArtifactVersionNewStageEvent(VersionActorEvent):
    event_type = ARTIFACT_VERSION_NEW_STAGE
    attributes = ARTIFACT_VERSION_ATTRIBUTES + (
        Attribute("stage"),
        Attribute("previous_stage", is_required=False),
    )
