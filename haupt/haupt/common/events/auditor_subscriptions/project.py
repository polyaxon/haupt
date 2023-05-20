from haupt.common import auditor
from haupt.common.events.registry import project

auditor.subscribe(project.ProjectCreatedActorEvent)
auditor.subscribe(project.ProjectUpdatedActorEvent)
auditor.subscribe(project.ProjectViewedActorEvent)
auditor.subscribe(project.ProjectSettingsActorEvent)
auditor.subscribe(project.ProjectDeletedActorEvent)
auditor.subscribe(project.ProjectStatsActorEvent)
auditor.subscribe(project.ProjectRunsViewedActorEvent)
