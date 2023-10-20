from clipped.utils.imports import import_string

from haupt.common.events.event_service import EventService
from haupt.common.events.registry import run
from haupt.orchestration.executor.manager import event_manager


class ExecutorService(EventService):
    event_manager = event_manager

    def __init__(self, workers_service=None, handlers_service=None):
        self.workers_service = workers_service
        self.handlers_service = handlers_service
        self.workers = None
        self.handlers = None
        self.handlers_mapping = None

    def record_event(self, event: "Event") -> None:  # noqa: F821
        if self.workers and event.event_type in self.handlers_mapping:
            self.handlers_mapping[event.event_type](
                workers_backend=self.workers, event=event
            )

    @staticmethod
    def _get_handler_mapping(handlers):
        return {
            run.RUN_CREATED: handlers.handle_run_created,
            run.RUN_RESUMED_ACTOR: handlers.handle_run_created,
            run.RUN_APPROVED_ACTOR: handlers.handle_run_approved_triggered,
            run.RUN_STOPPED_ACTOR: handlers.handle_run_stopped_triggered,
            run.RUN_SKIPPED_ACTOR: handlers.handle_run_skipped_triggered,
            run.RUN_NEW_ARTIFACTS: handlers.handle_new_artifacts,
            run.RUN_DELETED_ACTOR: handlers.handle_run_deleted,
            run.RUN_NEW_STATUS: handlers.handle_run_new_status,
            run.RUN_DONE: handlers.handle_run_done,
        }

    def setup(self) -> None:
        super().setup()
        # Load default event types
        import haupt.orchestration.executor.subscriptions  # noqa

        if self.workers_service:
            self.workers = import_string(self.workers_service)
        if self.handlers_service:
            self.handlers = import_string(self.handlers_service)
            self.handlers_mapping = self._get_handler_mapping(self.handlers)
