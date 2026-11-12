from mock import patch
import pytest

from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.db.defs import Models
from haupt.db.factories.runs import RunFactory
from haupt.orchestration.scheduler.manager import SchedulingManager
from polyaxon.schemas import (
    ManagedBy,
    V1RunEdgeKind,
    V1RunKind,
    V1RunPending,
    V1Statuses,
)
from tests.test_background.case import BaseTest


@pytest.mark.background_mark
class TestRunsNotifyStatus(BaseTest):
    def setUp(self):
        super().setUp()
        patcher = patch("haupt.common.workers.send")
        self.send = patcher.start()
        self.addCleanup(patcher.stop)
        self.dag = self._run(kind=V1RunKind.DAG, status=V1Statuses.RUNNING)
        self.upstream = self._run(pipeline=self.dag, status=V1Statuses.RUNNING)

    def _run(self, **kwargs):
        # Managed runs need a specification (`run_created` signal)
        return RunFactory(
            project=self.project,
            user=self.user,
            managed_by=ManagedBy.AGENT,
            raw_content="test",
            **kwargs,
        )

    def _downstream(self, upstream=None, statuses=(V1Statuses.RUNNING,), **kwargs):
        downstream = self._run(**kwargs)
        Models.RunEdge.objects.create(
            upstream=upstream or self.upstream,
            downstream=downstream,
            kind=V1RunEdgeKind.DAG,
            statuses=list(statuses) if statuses else None,
        )
        return downstream

    def _notify(self, run):
        self.send.reset_mock()
        SchedulingManager.runs_notify_status(run_id=run.id)

    def test_prepare_downstream_waiting_on_the_status(self):
        downstream = self._downstream(pipeline=self.dag)
        self._notify(self.upstream)
        # The id only, `runs_prepare` loads the run itself in eager mode
        self.send.assert_called_once_with(
            SchedulerCeleryTasks.RUNS_PREPARE, kwargs={"run_id": downstream.id}
        )

    def test_skip_downstream_not_waiting_on_the_status(self):
        self._downstream(pipeline=self.dag, pending=V1RunPending.APPROVAL)
        self._downstream(pipeline=self.dag, statuses=[V1Statuses.SUCCEEDED])
        self._downstream(pipeline=self.dag, statuses=None)
        self._downstream(pipeline=self.dag, status=V1Statuses.COMPILED)
        self._notify(self.upstream)
        assert self.send.call_count == 0

    def test_skip_upstream_outside_a_pipeline(self):
        upstream = self._run(status=V1Statuses.RUNNING)
        self._downstream(upstream=upstream)
        self._notify(upstream)
        assert self.send.call_count == 0
