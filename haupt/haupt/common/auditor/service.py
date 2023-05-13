import copy

from clipped.utils.imports import import_string

from haupt.common.auditor.manager import event_manager
from haupt.common.events.event import Event
from haupt.common.events.event_service import EventService


class AuditorService(EventService):
    """A service that just passes the event to other services."""

    event_manager = event_manager

    def __init__(
        self, auditor_events_task=None, workers_service=None, executor_service=None
    ):
        self.auditor_events_task = auditor_events_task
        self.executor = None
        self.workers = None
        self.workers_service = workers_service
        self.executor_service = executor_service

    def record_event(self, event: Event):
        """
        Record the event async.
        """
        serialized_event = event.serialize(
            dumps=False, include_actor_name=True, include_instance_info=True
        )
        if self.workers and self.auditor_events_task:
            self.workers.send(
                self.auditor_events_task,
                kwargs={"event": copy.deepcopy(serialized_event)},
            )

        if self.executor:
            # We include the instance in the serialized event for executor
            serialized_event["instance"] = event.instance
            self.executor.record(
                event_type=event.event_type, event_data=serialized_event
            )

    def setup(self):
        super().setup()

        if self.workers_service:
            self.workers = import_string(self.workers_service)
        if self.executor_service:
            self.executor = import_string(self.executor_service)
