from haupt.common.events import event_actions, event_subjects
from haupt.common.events.event import ActorEvent, ActorTopEntityEvent
from haupt.common.events.registry.attributes import (
    PROJECT_OWNER_ATTRIBUTES,
    PROJECT_RESOURCE_OWNER_ATTRIBUTES,
)

PROJECT_BOOKMARKED_ACTOR = "{}.{}.{}".format(
    event_subjects.PROJECT, event_actions.BOOKMARKED, event_subjects.ACTOR
)
PROJECT_UNBOOKMARKED_ACTOR = "{}.{}.{}".format(
    event_subjects.PROJECT, event_actions.UNBOOKMARKED, event_subjects.ACTOR
)
RUN_BOOKMARKED_ACTOR = "{}.{}.{}".format(
    event_subjects.RUN, event_actions.BOOKMARKED, event_subjects.ACTOR
)
RUN_UNBOOKMARKED_ACTOR = "{}.{}.{}".format(
    event_subjects.RUN, event_actions.UNBOOKMARKED, event_subjects.ACTOR
)

EVENTS = {
    PROJECT_BOOKMARKED_ACTOR,
    PROJECT_UNBOOKMARKED_ACTOR,
    RUN_BOOKMARKED_ACTOR,
    RUN_UNBOOKMARKED_ACTOR,
}


class ProjectBookmarkedActorEvent(ActorTopEntityEvent):
    event_type = PROJECT_BOOKMARKED_ACTOR
    attributes = PROJECT_OWNER_ATTRIBUTES


class ProjectUnBookmarkedActorEvent(ActorTopEntityEvent):
    event_type = PROJECT_UNBOOKMARKED_ACTOR
    attributes = PROJECT_OWNER_ATTRIBUTES


class RunBookmarkedActorEvent(ActorEvent):
    event_type = RUN_BOOKMARKED_ACTOR
    entity_uuid = "project.uuid"
    attributes = PROJECT_RESOURCE_OWNER_ATTRIBUTES


class RunUnBookmarkedActorEvent(ActorEvent):
    event_type = RUN_UNBOOKMARKED_ACTOR
    entity_uuid = "project.uuid"
    attributes = PROJECT_RESOURCE_OWNER_ATTRIBUTES
