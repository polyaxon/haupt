import pytest

from mock import mock

from haupt.db.factories.runs import RunFactory
from haupt.db.managers.statuses import new_run_status
from haupt.orchestration.scheduler.manager import SchedulingManager
from polyaxon.schemas import V1StatusCondition, V1Statuses
from tests.test_background.case import BaseTest


@pytest.mark.background_mark
class TestRunsStart(BaseTest):
    def test_start_run_not_queued(self):
        experiment = RunFactory(project=self.project, user=self.user)
        SchedulingManager.runs_start(run_id=experiment.id)
        new_run_status(
            run=experiment,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.RUNNING, status=True
            ),
        )
        SchedulingManager.runs_start(run_id=experiment.id)

    @mock.patch("haupt.orchestration.scheduler.manager.SchedulingManager.runs_start")
    def test_start_run(self, manager_start):
        experiment = RunFactory(project=self.project, user=self.user)
        new_run_status(
            run=experiment,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.COMPILED, status=True
            ),
        )
        SchedulingManager.runs_start(run_id=experiment.id)
        assert manager_start.call_count == 1
