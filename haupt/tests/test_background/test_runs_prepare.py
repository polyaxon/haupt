import pytest

from mock import MagicMock, mock, patch

from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.db.factories.runs import RunFactory
from haupt.db.managers.statuses import new_run_status
from haupt.orchestration.scheduler.manager import SchedulingManager
from polyaxon.lifecycle import ManagedBy, V1StatusCondition, V1Statuses
from polyaxon.polyflow import V1Cache
from tests.test_background.case import BaseTest


@pytest.mark.background_mark
class TestRunsPrepare(BaseTest):
    def setUp(self):
        super().setUp()
        patcher = patch(
            "haupt.orchestration.scheduler.manager.SchedulingManager.runs_start"
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "haupt.orchestration.scheduler.manager.SchedulingManager.runs_stop"
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @mock.patch("haupt.orchestration.scheduler.manager.SchedulingManager._resolve")
    def test_prepare_run_of_already_queued_run(self, mock_resolve):
        spec_run = MagicMock(cache=None)
        mock_resolve.return_value = (None, spec_run)

        experiment = RunFactory(project=self.project, user=self.user)
        new_run_status(
            run=experiment,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.QUEUED, status=True
            ),
        )

        new_experiment = RunFactory(project=self.project, user=self.user)
        SchedulingManager.runs_prepare(run_id=new_experiment.id)

        new_experiment.refresh_from_db()
        assert new_experiment.status == V1Statuses.COMPILED

    @mock.patch("haupt.orchestration.scheduler.manager.SchedulingManager._resolve")
    def test_prepare_run_of_already_stopped_run(self, mock_resolve):
        spec_run = MagicMock(cache=V1Cache(disable=False))
        mock_resolve.return_value = (None, spec_run)

        experiment = RunFactory(project=self.project, user=self.user)
        new_run_status(
            run=experiment,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.STOPPED, status=True
            ),
        )

        new_experiment = RunFactory(project=self.project, user=self.user)
        SchedulingManager.runs_prepare(run_id=new_experiment.id)

        new_experiment.refresh_from_db()
        assert new_experiment.status == V1Statuses.COMPILED

    @mock.patch("haupt.orchestration.scheduler.manager.SchedulingManager._resolve")
    def test_prepare_run_of_already_stopping_run(self, mock_resolve):
        spec_run = MagicMock(cache=V1Cache(disable=False))
        mock_resolve.return_value = (None, spec_run)

        experiment = RunFactory(project=self.project, user=self.user)
        new_run_status(
            run=experiment,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.STOPPING, status=True
            ),
        )

        new_experiment = RunFactory(project=self.project, user=self.user)
        SchedulingManager.runs_prepare(run_id=new_experiment.id)

        new_experiment.refresh_from_db()
        assert new_experiment.status == V1Statuses.COMPILED

    @mock.patch("haupt.orchestration.scheduler.manager.SchedulingManager._resolve")
    def test_prepare_run_of_already_skipped_run(self, mock_resolve):
        spec_run = MagicMock(cache=V1Cache(disable=False))
        mock_resolve.return_value = (None, spec_run)

        experiment = RunFactory(project=self.project, user=self.user)
        new_run_status(
            run=experiment,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.SKIPPED, status=True
            ),
        )

        new_experiment = RunFactory(project=self.project, user=self.user)
        SchedulingManager.runs_prepare(run_id=new_experiment.id)

        new_experiment.refresh_from_db()
        assert new_experiment.status == V1Statuses.COMPILED

    @mock.patch("haupt.orchestration.scheduler.manager.SchedulingManager._resolve")
    def test_prepare_run_of_already_failed_run(self, mock_resolve):
        spec_run = MagicMock(cache=V1Cache(disable=False))
        mock_resolve.return_value = (None, spec_run)

        experiment = RunFactory(project=self.project, user=self.user)
        new_run_status(
            run=experiment,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.FAILED, status=True
            ),
        )

        new_experiment = RunFactory(project=self.project, user=self.user)
        SchedulingManager.runs_prepare(run_id=new_experiment.id)

        new_experiment.refresh_from_db()
        assert new_experiment.status == V1Statuses.COMPILED

    @mock.patch("haupt.common.workers.send")
    @mock.patch("haupt.orchestration.scheduler.manager.SchedulingManager._resolve")
    def test_prepare_run_of_already_failed_run_mock(self, mock_resolve, send_mock):
        with mock.patch("django.db.transaction.on_commit", lambda t: t()):
            spec_run = MagicMock(cache=V1Cache(disable=True))
            mock_resolve.return_value = (None, spec_run)
            experiment = RunFactory(
                project=self.project,
                user=self.user,
                raw_content="test",
                managed_by=ManagedBy.AGENT,
            )
            # We are patching the automatic call and executing prepare manually
            SchedulingManager.runs_prepare(run_id=experiment.id)
            experiment.refresh_from_db()
            assert experiment.status == V1Statuses.COMPILED
            assert send_mock.call_count == 2  # runs_prepare and runs_start
            assert {
                c[0][0]: c[1].get("delay", False) for c in send_mock.call_args_list
            } == {
                SchedulerCeleryTasks.RUNS_START: False,
                SchedulerCeleryTasks.RUNS_PREPARE: True,
            }
