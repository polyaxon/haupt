from haupt.common.events import event_actions, event_subjects
from haupt.common.events.event import ActorTopEntityEvent
from haupt.common.events.registry.attributes import PROJECT_OWNER_ATTRIBUTES

PROJECT_CREATED_ACTOR = "{}.{}.{}".format(
    event_subjects.PROJECT, event_actions.CREATED, event_subjects.ACTOR
)
PROJECT_UPDATED_ACTOR = "{}.{}.{}".format(
    event_subjects.PROJECT, event_actions.UPDATED, event_subjects.ACTOR
)
PROJECT_SETTINGS_ACTOR = "{}.{}.{}".format(
    event_subjects.PROJECT, event_actions.SETTINGS, event_subjects.ACTOR
)
PROJECT_DELETED_ACTOR = "{}.{}.{}".format(
    event_subjects.PROJECT, event_actions.DELETED, event_subjects.ACTOR
)
PROJECT_VIEWED_ACTOR = "{}.{}.{}".format(
    event_subjects.PROJECT, event_actions.VIEWED, event_subjects.ACTOR
)
PROJECT_RUNS_VIEWED_ACTOR = "{}.{}.{}".format(
    event_subjects.PROJECT, event_actions.RUNS_VIEWED, event_subjects.ACTOR
)
PROJECT_STATS_ACTOR = "{}.{}.{}".format(
    event_subjects.PROJECT, event_actions.STATS, event_subjects.ACTOR
)

EVENTS = {
    PROJECT_CREATED_ACTOR,
    PROJECT_UPDATED_ACTOR,
    PROJECT_SETTINGS_ACTOR,
    PROJECT_VIEWED_ACTOR,
    PROJECT_DELETED_ACTOR,
    PROJECT_RUNS_VIEWED_ACTOR,
    PROJECT_STATS_ACTOR,
}


class ProjectCreatedActorEvent(ActorTopEntityEvent):
    event_type = PROJECT_CREATED_ACTOR
    attributes = PROJECT_OWNER_ATTRIBUTES


class ProjectUpdatedActorEvent(ActorTopEntityEvent):
    event_type = PROJECT_UPDATED_ACTOR
    attributes = PROJECT_OWNER_ATTRIBUTES


class ProjectSettingsActorEvent(ActorTopEntityEvent):
    event_type = PROJECT_SETTINGS_ACTOR
    attributes = PROJECT_OWNER_ATTRIBUTES


class ProjectDeletedActorEvent(ActorTopEntityEvent):
    event_type = PROJECT_DELETED_ACTOR
    attributes = PROJECT_OWNER_ATTRIBUTES


class ProjectViewedActorEvent(ActorTopEntityEvent):
    event_type = PROJECT_VIEWED_ACTOR
    attributes = PROJECT_OWNER_ATTRIBUTES


class ProjectRunsViewedActorEvent(ActorTopEntityEvent):
    event_type = PROJECT_RUNS_VIEWED_ACTOR
    attributes = PROJECT_OWNER_ATTRIBUTES


class ProjectStatsActorEvent(ActorTopEntityEvent):
    event_type = PROJECT_STATS_ACTOR
    attributes = PROJECT_OWNER_ATTRIBUTES
