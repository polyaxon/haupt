from haupt.common import auditor
from haupt.common.events.registry import archive

auditor.subscribe(archive.ProjectArchivedActorEvent)
auditor.subscribe(archive.ProjectRestoredActorEvent)
auditor.subscribe(archive.RunArchivedActorEvent)
auditor.subscribe(archive.RunRestoredActorEvent)
