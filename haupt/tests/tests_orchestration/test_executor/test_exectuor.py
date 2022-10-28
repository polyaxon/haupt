#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from mock import MagicMock, patch

from django.test import TestCase

from haupt.background.celeryp.tasks import CoreSchedulerCeleryTasks
from haupt.common import auditor
from haupt.common.events.registry import run as run_events
from haupt.orchestration import executor
from haupt.orchestration.executor.handlers.run import (
    handle_run_created,
    handle_run_stopped_triggered,
)
from polyaxon.constants.metadata import META_EAGER_MODE
from polyaxon.schemas import V1RunPending


class States:
    workers = None


class DummyWorkers:
    @staticmethod
    def send(task, **kwargs):
        States.workers = {"task": task}
        States.workers.update(kwargs)


class TestExecutorRecord(TestCase):
    def setUp(self):
        super().setUp()
        from haupt.common.events import auditor_subscriptions  # noqa
        from haupt.orchestration.executor import subscriptions  # noqa

        executor.validate_and_setup()
        auditor.validate_and_setup()
        self.user = MagicMock(id=1)
        self.owner = MagicMock(id=1, name="owner")
        self.project = MagicMock(id=1, owner=self.owner, name="project")

    @patch("haupt.orchestration.executor.service.ExecutorService.record")
    def test_create_run_creation_is_recorded_by_executor(self, executor_record):
        run = MagicMock(project=self.project)
        auditor.record(run_events.RUN_CREATED, instance=run)
        assert executor_record.call_count == 1
        call_args, call_kwargs = executor_record.call_args
        assert call_kwargs["event_type"] == run_events.RUN_CREATED


class TestExecutorHandlers(TestCase):
    def setUp(self):
        super().setUp()
        from haupt.common.events import auditor_subscriptions  # noqa
        from haupt.orchestration.executor import subscriptions  # noqa

        auditor.validate_and_setup()
        self.user = MagicMock(id=1)
        self.owner = MagicMock(id=1, name="owner")
        self.project = MagicMock(id=1, owner=self.owner, name="project")

    def test_create_run_handler_non_managed_run(self):
        States.workers = None
        event = MagicMock(data={"is_managed": False})
        handle_run_created(None, event=event)
        assert States.workers is None

    def test_create_run_handler_pipeline_run(self):
        States.workers = None
        data = {"is_managed": True, "pipeline_id": 1}
        event = MagicMock(data=data)
        handle_run_created(None, event=event)
        assert States.workers is None

    def test_create_run_handler(self):
        States.workers = None
        data = {"id": 1, "is_managed": True, "pipeline_id": None}
        event = MagicMock(data=data, instance=MagicMock(meta_info=None, pending=None))
        handle_run_created(DummyWorkers, event=event)
        assert States.workers["task"] == CoreSchedulerCeleryTasks.RUNS_PREPARE

        States.workers = None
        event = MagicMock(data=data, instance=MagicMock(meta_info={}, pending=None))
        handle_run_created(DummyWorkers, event=event)
        assert States.workers["task"] == CoreSchedulerCeleryTasks.RUNS_PREPARE

        States.workers = None
        event = MagicMock(
            data=data,
            instance=MagicMock(
                meta_info={"is_approved": False}, pending=V1RunPending.APPROVAL
            ),
        )
        handle_run_created(DummyWorkers, event=event)
        assert States.workers is None

        States.workers = None
        event = MagicMock(
            data=data,
            instance=MagicMock(
                meta_info={"is_approved": False}, pending=V1RunPending.UPLOAD
            ),
        )
        handle_run_created(DummyWorkers, event=event)
        assert States.workers is None

        States.workers = None
        event = MagicMock(
            data=data,
            instance=MagicMock(
                meta_info={"is_approved": False}, pending=V1RunPending.BUILD
            ),
        )
        handle_run_created(DummyWorkers, event=event)
        assert States.workers is None

        States.workers = None
        event = MagicMock(
            data=data, instance=MagicMock(meta_info={"is_approved": True}, pending=None)
        )
        handle_run_created(DummyWorkers, event=event)
        assert States.workers["task"] == CoreSchedulerCeleryTasks.RUNS_PREPARE

        States.workers = None
        event = MagicMock(
            data=data,
            instance=MagicMock(meta_info={META_EAGER_MODE: False}, pending=None),
        )
        handle_run_created(DummyWorkers, event=event)
        assert States.workers["task"] == CoreSchedulerCeleryTasks.RUNS_PREPARE

        States.workers = None
        event = MagicMock(
            data=data,
            instance=MagicMock(meta_info={META_EAGER_MODE: True}, pending=None),
        )
        handle_run_created(DummyWorkers, event=event)
        assert States.workers is None

    def test_stop_run_handler_managed_run(self):
        States.workers = None
        event = MagicMock(data={"id": 1, "is_managed": True})
        handle_run_stopped_triggered(DummyWorkers, event=event)
        assert States.workers["task"] == CoreSchedulerCeleryTasks.RUNS_STOP
