from unittest.mock import patch

from django.test import TestCase

from haupt.common.events.registry import run as run_events
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.factories.users import UserFactory
from haupt.db.managers.statuses import bulk_new_run_status, new_run_status
from haupt.db.models.runs import Run
from polyaxon.schemas import ManagedBy, V1RunKind, V1StatusCondition, V1Statuses


class TestRunStatusManager(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()
        self.run = RunFactory(project=self.project)

    @patch("haupt.common.auditor.record")
    def test_new_run_status_created(self, auditor_record):
        new_run_status(
            self.run,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.CREATED, status=True
            ),
        )
        assert auditor_record.call_count == 0

    @patch("haupt.common.auditor.record")
    def test_new_run_status_scheduled(self, auditor_record):
        new_run_status(
            self.run,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.SCHEDULED, status=True
            ),
        )
        assert auditor_record.call_count == 1
        call_args, call_kwargs = auditor_record.call_args
        assert call_args == ()
        assert call_kwargs["event_type"] == run_events.RUN_NEW_STATUS

    @patch("haupt.common.auditor.record")
    def test_new_run_status_stopped(self, auditor_record):
        new_run_status(
            self.run,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.STOPPED, status=True
            ),
        )
        assert auditor_record.call_count == 3
        call_args_list = auditor_record.call_args_list
        assert call_args_list[0][0] == ()
        assert call_args_list[1][0] == ()
        assert call_args_list[2][0] == ()
        assert call_args_list[0][1]["event_type"] == run_events.RUN_NEW_STATUS
        assert call_args_list[1][1]["event_type"] == run_events.RUN_STOPPED
        assert call_args_list[2][1]["event_type"] == run_events.RUN_DONE

    @patch("haupt.common.auditor.record")
    def test_new_run_status_failed(self, auditor_record):
        new_run_status(
            self.run,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.FAILED, status=True
            ),
        )
        assert auditor_record.call_count == 3
        call_args_list = auditor_record.call_args_list
        assert call_args_list[0][0] == ()
        assert call_args_list[1][0] == ()
        assert call_args_list[2][0] == ()
        assert call_args_list[0][1]["event_type"] == run_events.RUN_NEW_STATUS
        assert call_args_list[1][1]["event_type"] == run_events.RUN_FAILED
        assert call_args_list[2][1]["event_type"] == run_events.RUN_DONE

    @patch("haupt.common.auditor.record")
    def test_new_run_status_succeeded(self, auditor_record):
        new_run_status(
            self.run,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.SUCCEEDED, status=True
            ),
        )
        assert auditor_record.call_count == 3
        call_args_list = auditor_record.call_args_list
        assert call_args_list[0][0] == ()
        assert call_args_list[1][0] == ()
        assert call_args_list[2][0] == ()
        assert call_args_list[0][1]["event_type"] == run_events.RUN_NEW_STATUS
        assert call_args_list[1][1]["event_type"] == run_events.RUN_SUCCEEDED
        assert call_args_list[2][1]["event_type"] == run_events.RUN_DONE

    @patch("haupt.common.auditor.record")
    def test_new_run_status_skipped(self, auditor_record):
        new_run_status(
            self.run,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.SKIPPED, status=True
            ),
        )
        assert auditor_record.call_count == 3
        call_args_list = auditor_record.call_args_list
        assert call_args_list[0][0] == ()
        assert call_args_list[1][0] == ()
        assert call_args_list[2][0] == ()
        assert call_args_list[0][1]["event_type"] == run_events.RUN_NEW_STATUS
        assert call_args_list[1][1]["event_type"] == run_events.RUN_SKIPPED
        assert call_args_list[2][1]["event_type"] == run_events.RUN_DONE

    def test_bulk_run_status(self):
        run1 = RunFactory(project=self.project, kind=V1RunKind.JOB)
        run2 = RunFactory(project=self.project, kind=V1RunKind.JOB)
        run3 = RunFactory(project=self.project, kind=V1RunKind.SERVICE)
        # Patch all runs to be managed
        Run.all.update(managed_by=ManagedBy.AGENT)
        assert run1.status != V1Statuses.QUEUED
        assert run2.status != V1Statuses.QUEUED
        assert run3.status != V1Statuses.QUEUED

        condition = V1StatusCondition.get_condition(
            type=V1Statuses.QUEUED,
            status="True",
            reason="PolyaxonRunQueued",
            message="Run is queued",
        )
        bulk_new_run_status([run1, run2, run3], condition)
        run1.refresh_from_db()
        assert run1.status == V1Statuses.QUEUED
        run2.refresh_from_db()
        assert run2.status == V1Statuses.QUEUED
        run3.refresh_from_db()
        assert run3.status == V1Statuses.QUEUED
