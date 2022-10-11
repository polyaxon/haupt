#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from mock import MagicMock
from unittest import TestCase

from haupt.common.auditor.service import AuditorService
from haupt.common.events.registry.run import RUN_SUCCEEDED, RunSucceededEvent


class States:
    workers = None
    executor = None


class DummyWorkers:
    @staticmethod
    def send(task, **kwargs):
        States.workers = {"task": task}
        States.workers.update(kwargs)


class DummyExecutor:
    @staticmethod
    def record(**kwargs):
        States.executor = kwargs


class DummyAuditorService(AuditorService):
    pass


class TestAuditor(TestCase):
    def test_auditor_with_no_backends_record_events(self):
        States.executor = None
        States.workers = None
        auditor = DummyAuditorService()
        auditor.validate_and_setup()
        auditor.event_manager.subscribe(RunSucceededEvent)

        instance = MagicMock()
        serialized_event = auditor.record(
            event_type=RUN_SUCCEEDED, actor_id=1, actor_name="user", instance=instance
        )

        assert States.executor is None
        assert States.workers is None
        assert serialized_event.event_type == RunSucceededEvent.event_type

    def test_auditor_with_executor_backends_record_events(self):
        States.executor = None
        States.workers = None
        auditor = DummyAuditorService(
            executor_service="tests.tests_common.test_auditor.test_auditor.DummyExecutor"
        )
        auditor.validate_and_setup()
        auditor.event_manager.subscribe(RunSucceededEvent)

        instance = MagicMock(uuid="uuid")
        serialized_event = auditor.record(
            event_type=RUN_SUCCEEDED,
            actor_id=1,
            actor_name="user",
            project_id=1,
            project_name=13,
            project_owner_id=12,
            project_owner_name="foo",
            instance=instance,
        )

        assert States.workers is None
        assert States.executor["event_type"] == RUN_SUCCEEDED
        assert States.executor["event_data"] is not None
        assert serialized_event.event_type == RunSucceededEvent.event_type

    def test_auditor_with_workers_backends_record_events_without_task(self):
        States.executor = None
        States.workers = None
        auditor = DummyAuditorService(
            workers_service="tests.tests_common.test_auditor.test_auditor.DummyWorkers"
        )
        auditor.validate_and_setup()
        auditor.event_manager.subscribe(RunSucceededEvent)

        instance = MagicMock(uuid="uuid")
        serialized_event = auditor.record(
            event_type=RUN_SUCCEEDED,
            actor_id=1,
            actor_name="user",
            project_id=1,
            project_name=13,
            project_owner_id=12,
            project_owner_name="foo",
            instance=instance,
        )

        assert States.executor is None
        assert States.workers is None
        assert serialized_event.event_type == RunSucceededEvent.event_type

    def test_auditor_with_workers_backends_record_events_and_task(self):
        States.executor = None
        States.workers = None
        auditor = DummyAuditorService(
            workers_service="tests.tests_common.test_auditor.test_auditor.DummyWorkers",
            auditor_events_task="foo.bar",
        )
        auditor.validate_and_setup()
        auditor.event_manager.subscribe(RunSucceededEvent)

        instance = MagicMock(uuid="uuid")
        serialized_event = auditor.record(
            event_type=RUN_SUCCEEDED,
            actor_id=1,
            actor_name="user",
            project_id=1,
            project_name=13,
            project_owner_id=12,
            project_owner_name="foo",
            instance=instance,
        )

        assert States.executor is None
        assert States.workers["task"] == "foo.bar"
        assert States.workers["kwargs"]["event"] is not None
        assert States.workers["kwargs"]["event"]["type"] == RunSucceededEvent.event_type
        assert serialized_event.event_type == RunSucceededEvent.event_type

    def test_auditor_with_workers_backends_and_executor_backend(self):
        States.executor = None
        States.workers = None
        auditor = DummyAuditorService(
            executor_service="tests.tests_common.test_auditor.test_auditor.DummyExecutor",
            workers_service="tests.tests_common.test_auditor.test_auditor.DummyWorkers",
            auditor_events_task="foo.bar",
        )
        auditor.validate_and_setup()
        auditor.event_manager.subscribe(RunSucceededEvent)

        instance = MagicMock(uuid="uuid")
        serialized_event = auditor.record(
            event_type=RUN_SUCCEEDED,
            actor_id=1,
            actor_name="user",
            project_id=1,
            project_name=13,
            project_owner_id=12,
            project_owner_name="foo",
            instance=instance,
        )

        assert States.executor["event_type"] == RUN_SUCCEEDED
        assert States.executor["event_data"] is not None
        assert States.workers["task"] == "foo.bar"
        assert States.workers["kwargs"]["event"] is not None
        assert States.workers["kwargs"]["event"]["type"] == RunSucceededEvent.event_type
        assert serialized_event.event_type == RunSucceededEvent.event_type
