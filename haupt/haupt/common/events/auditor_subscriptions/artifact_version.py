from haupt.common import auditor
from haupt.common.events.registry import artifact_version

auditor.subscribe(artifact_version.ArtifactVersionDeletedEvent)
auditor.subscribe(artifact_version.ArtifactVersionCreatedActorEvent)
auditor.subscribe(artifact_version.ArtifactVersionUpdatedActorEvent)
auditor.subscribe(artifact_version.ArtifactVersionViewedActorEvent)
auditor.subscribe(artifact_version.ArtifactVersionDeletedActorEvent)
auditor.subscribe(artifact_version.ArtifactVersionTransferredActorEvent)
auditor.subscribe(artifact_version.ArtifactVersionNewStageEvent)