from haupt.common.events import event_actions, event_subjects
from haupt.common.events.event import ActorEvent, ActorTopEntityEvent
from haupt.common.events.registry.attributes import (
    PROJECT_OWNER_ATTRIBUTES,
    PROJECT_RESOURCE_OWNER_ATTRIBUTES,
)

PROJECT_ARCHIVED_ACTOR = "{}.{}.{}".format(
    event_subjects.PROJECT, event_actions.ARCHIVED, event_subjects.ACTOR
)
PROJECT_RESTORED_ACTOR = "{}.{}.{}".format(
    event_subjects.PROJECT, event_actions.RESTORED, event_subjects.ACTOR
)
RUN_ARCHIVED_ACTOR = "{}.{}.{}".format(
    event_subjects.RUN, event_actions.ARCHIVED, event_subjects.ACTOR
)
RUN_RESTORED_ACTOR = "{}.{}.{}".format(
    event_subjects.RUN, event_actions.RESTORED, event_subjects.ACTOR
)

EVENTS = {
    PROJECT_ARCHIVED_ACTOR,
    PROJECT_RESTORED_ACTOR,
    RUN_ARCHIVED_ACTOR,
    RUN_RESTORED_ACTOR,
}


class ProjectArchivedActorEvent(ActorTopEntityEvent):
    event_type = PROJECT_ARCHIVED_ACTOR
    actor = True
    attributes = PROJECT_OWNER_ATTRIBUTES


class ProjectRestoredActorEvent(ActorTopEntityEvent):
    event_type = PROJECT_RESTORED_ACTOR
    actor = True
    attributes = PROJECT_OWNER_ATTRIBUTES


class RunArchivedActorEvent(ActorEvent):
    event_type = RUN_ARCHIVED_ACTOR
    actor = True
    entity_uuid = "project.uuid"
    attributes = PROJECT_RESOURCE_OWNER_ATTRIBUTES


class RunRestoredActorEvent(ActorEvent):
    event_type = RUN_RESTORED_ACTOR
    actor = True
    entity_uuid = "project.uuid"
    attributes = PROJECT_RESOURCE_OWNER_ATTRIBUTES
