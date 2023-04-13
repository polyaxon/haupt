#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from clipped.utils.imports import import_string

from haupt.common.events.event_service import EventService
from haupt.common.events.registry import run
from haupt.orchestration.executor.handlers import run as run_handlers
from haupt.orchestration.executor.manager import event_manager


class ExecutorService(EventService):
    HANDLER_MAPPING = {
        run.RUN_CREATED: run_handlers.handle_run_created,
        run.RUN_RESUMED_ACTOR: run_handlers.handle_run_created,
        run.RUN_APPROVED_ACTOR: run_handlers.handle_run_approved_triggered,
        run.RUN_STOPPED_ACTOR: run_handlers.handle_run_stopped_triggered,
        run.RUN_NEW_ARTIFACTS: run_handlers.handle_new_artifacts,
        run.RUN_DELETED_ACTOR: run_handlers.handle_run_deleted,
    }

    event_manager = event_manager

    def __init__(self, workers_service=None):
        self.workers_service = workers_service
        self.workers = None

    def record_event(self, event: "Event") -> None:  # noqa: F821
        if self.workers and event.event_type in self.HANDLER_MAPPING:
            self.HANDLER_MAPPING[event.event_type](
                workers_backend=self.workers, event=event
            )

    def setup(self) -> None:
        super().setup()
        # Load default event types
        import haupt.orchestration.executor.subscriptions  # noqa

        if self.workers_service:
            self.workers = import_string(self.workers_service)
