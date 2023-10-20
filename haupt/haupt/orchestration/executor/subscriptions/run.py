from haupt.common.events.registry import run
from haupt.orchestration import executor

executor.subscribe(run.RunCreatedEvent)
executor.subscribe(run.RunResumedActorEvent)
executor.subscribe(run.RunStoppedActorEvent)
executor.subscribe(run.RunSkippedActorEvent)
executor.subscribe(run.RunApprovedActorEvent)
executor.subscribe(run.RunNewStatusEvent)
executor.subscribe(run.RunDoneEvent)
executor.subscribe(run.RunDeletedActorEvent)
executor.subscribe(run.RunNewArtifactsEvent)
