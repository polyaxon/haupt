from datetime import timedelta
from mock import patch
import pytest

from django.utils.timezone import now

from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.db.defs import Models
from haupt.db.factories.runs import RunFactory
from haupt.orchestration import operations
from haupt.orchestration.scheduler.manager import SchedulingManager
from polyaxon.schemas import (
    ManagedBy,
    V1CloningKind,
    V1MatrixKind,
    V1RunEdgeKind,
    V1RunKind,
    V1RunPending,
    V1Statuses,
)
from tests.test_background.case import BaseTest


PREPARE = SchedulerCeleryTasks.RUNS_PREPARE
START = SchedulerCeleryTasks.RUNS_START
CHECK_PIPELINE = SchedulerCeleryTasks.RUNS_CHECK_PIPELINE


@pytest.mark.background_mark
class TestReconcileRuns(BaseTest):
    def setUp(self):
        super().setUp()
        patcher = patch("haupt.common.workers.send")
        self.send = patcher.start()
        self.addCleanup(patcher.stop)

    def _run(self, **kwargs):
        # Managed runs need a specification (`run_created` signal)
        kwargs.setdefault("managed_by", ManagedBy.AGENT)
        kwargs.setdefault("raw_content", "test")
        return RunFactory(project=self.project, user=self.user, **kwargs)

    @staticmethod
    def _age(*runs, minutes: int = 10):
        Models.Run.objects.filter(id__in=[r.id for r in runs]).update(
            updated_at=now() - timedelta(minutes=minutes)
        )

    @staticmethod
    def _dag_edge(upstream, downstream):
        Models.RunEdge.objects.create(
            upstream=upstream, downstream=downstream, kind=V1RunEdgeKind.DAG
        )

    @staticmethod
    def _build_edge(builder, run):
        operations.save_build_relation(
            operations.OperationInitSpec(
                compiled_operation=None, instance=run, related_instance=builder
            )
        )

    def _reconcile(self, **kwargs):
        self.send.reset_mock()
        SchedulingManager.reconcile_runs(**kwargs)
        return [(c[0][0], c[1]["kwargs"]["run_id"]) for c in self.send.call_args_list]

    def test_prepare_created_run(self):
        run = self._run()
        assert self._reconcile() == []

        self._age(run)
        assert self._reconcile() == [(PREPARE, run.id)]

    def test_prepare_resuming_and_on_schedule_runs(self):
        resuming = self._run(status=V1Statuses.RESUMING)
        on_schedule = self._run(status=V1Statuses.ON_SCHEDULE, schedule_at=now())
        self._age(resuming, on_schedule)
        assert set(self._reconcile()) == {
            (PREPARE, resuming.id),
            (PREPARE, on_schedule.id),
        }

    def test_prepare_skips_pending_scheduled_and_unmanaged_runs(self):
        pending = self._run(pending=V1RunPending.APPROVAL)
        scheduled = self._run(schedule_at=now() + timedelta(hours=1))
        unmanaged = self._run(managed_by=ManagedBy.USER)
        self._age(pending, scheduled, unmanaged)
        assert self._reconcile() == []

    def test_prepare_skips_pipeline_with_children(self):
        dag = self._run(kind=V1RunKind.DAG)
        self._run(pipeline=dag)
        self._age(dag)
        with self.assertLogs("polyaxon.scheduler", level="WARNING"):
            assert self._reconcile() == []

    def test_prepare_independent_child_once_pipeline_is_quiet(self):
        dag = self._run(kind=V1RunKind.DAG, status=V1Statuses.RUNNING)
        child = self._run(pipeline=dag)
        sibling = self._run(pipeline=dag, status=V1Statuses.COMPILED)
        self._age(dag, child)
        # A sibling was just compiled, staggered prepares may still be pending
        assert self._reconcile() == []

        self._age(sibling)
        assert self._reconcile() == [(PREPARE, child.id)]

    @patch.object(SchedulingManager, "_trigger_downstream")
    def test_trigger_child_once_every_upstream_is_done(self, trigger):
        dag = self._run(kind=V1RunKind.DAG, status=V1Statuses.RUNNING)
        upstream1 = self._run(pipeline=dag, status=V1Statuses.SUCCEEDED)
        upstream2 = self._run(pipeline=dag, status=V1Statuses.RUNNING)
        downstream = self._run(pipeline=dag)
        self._dag_edge(upstream1, downstream)
        self._dag_edge(upstream2, downstream)
        self._age(dag, upstream1, upstream2, downstream)
        self._reconcile()
        assert trigger.call_count == 0

        Models.Run.objects.filter(id=upstream2.id).update(status=V1Statuses.SKIPPED)
        self._age(upstream2)
        self._reconcile()
        assert trigger.call_count == 1
        assert [r.id for r in trigger.call_args[0][0]] == [downstream.id]
        assert trigger.call_args[1] == {"is_skipped": True}

    @patch.object(SchedulingManager, "_trigger_downstream")
    def test_prepare_built_child(self, trigger):
        dag = self._run(kind=V1RunKind.DAG, status=V1Statuses.RUNNING)
        upstream = self._run(pipeline=dag, status=V1Statuses.SUCCEEDED)
        builder = self._run(runtime=V1RunKind.BUILDER, status=V1Statuses.SUCCEEDED)
        child = self._run(pipeline=dag)
        self._dag_edge(upstream, child)
        self._build_edge(builder, child)
        self._age(dag, upstream, builder, child)
        assert self._reconcile() == [(PREPARE, child.id)]
        assert trigger.call_count == 0

    def test_start_compiled_runs(self):
        top = self._run(status=V1Statuses.COMPILED)
        schedule = self._run(kind=V1RunKind.SCHEDULE, status=V1Statuses.RUNNING)
        scheduled = self._run(
            pipeline=schedule, status=V1Statuses.COMPILED, schedule_at=now()
        )
        dag = self._run(kind=V1RunKind.DAG, status=V1Statuses.RUNNING)
        dag_child = self._run(pipeline=dag, status=V1Statuses.COMPILED)
        bayes = self._run(
            kind=V1RunKind.MATRIX,
            runtime=V1MatrixKind.BAYES,
            status=V1Statuses.COMPILED,
        )
        self._age(top, schedule, scheduled, dag, dag_child, bayes)
        assert set(self._reconcile()) == {(START, top.id), (START, scheduled.id)}

    def test_check_pipeline_with_done_children(self):
        dag = self._run(kind=V1RunKind.DAG, status=V1Statuses.RUNNING)
        dag_child = self._run(pipeline=dag, status=V1Statuses.SUCCEEDED)
        bayes = self._run(
            kind=V1RunKind.MATRIX,
            runtime=V1MatrixKind.BAYES,
            status=V1Statuses.RUNNING,
        )
        bayes_child = self._run(pipeline=bayes, status=V1Statuses.SUCCEEDED)
        empty = self._run(kind=V1RunKind.DAG, status=V1Statuses.RUNNING)
        self._age(dag, bayes, empty)
        # Children finished recently, their check may still be pending
        assert self._reconcile() == []

        self._age(dag_child, bayes_child)
        assert self._reconcile() == [(CHECK_PIPELINE, dag.id)]

    @patch.object(SchedulingManager, "_notify_build")
    def test_notify_done_builder(self, notify_build):
        builder = self._run(runtime=V1RunKind.BUILDER, status=V1Statuses.SUCCEEDED)
        run = self._run(pending=V1RunPending.BUILD)
        self._build_edge(builder, run)
        self._age(run)
        # Builder finished recently, its notification may still be pending
        self._reconcile()
        assert notify_build.call_count == 0

        self._age(builder)
        self._reconcile()
        assert [c[0][0].id for c in notify_build.call_args_list] == [builder.id]

    @patch.object(SchedulingManager, "_notify_cache")
    def test_notify_cache_skips_done_clones(self, notify_cache):
        stopped_original = self._run(status=V1Statuses.SUCCEEDED)
        # Managed clones need a compiled specification (`run_created` signal)
        stopped_clone = self._run(
            original=stopped_original,
            cloning_kind=V1CloningKind.CACHE,
            pending=V1RunPending.CACHE,
            status=V1Statuses.STOPPED,
            content="test",
        )
        original = self._run(status=V1Statuses.FAILED)
        clone = self._run(
            original=original,
            cloning_kind=V1CloningKind.CACHE,
            pending=V1RunPending.CACHE,
            content="test",
        )
        self._age(stopped_original, original, clone)
        self._age(stopped_clone, minutes=20)
        self._reconcile(limit=1)
        assert [c[0][0].id for c in notify_cache.call_args_list] == [original.id]

    def test_claimed_run_is_retried_after_threshold(self):
        run = self._run()
        self._age(run)
        assert self._reconcile() == [(PREPARE, run.id)]
        # Another sweep, or the next tick, finds the run claimed
        assert self._reconcile() == []
        # Still stuck once the claim is older than the threshold
        assert self._reconcile(minutes=0) == [(PREPARE, run.id)]

    def test_limit(self):
        runs = [self._run() for _ in range(3)]
        self._age(*runs)
        first = self._reconcile(limit=2)
        second = self._reconcile(limit=2)
        assert len(first) == 2
        assert {c[1] for c in first + second} == {r.id for r in runs}

    def test_failing_recovery_does_not_drop_the_batch(self):
        first = self._run()
        second = self._run()
        self._age(first, minutes=20)
        self._age(second)
        self.send.side_effect = [Exception("boom"), None]
        with self.assertLogs("polyaxon.scheduler", level="ERROR"):
            assert set(self._reconcile()) == {
                (PREPARE, first.id),
                (PREPARE, second.id),
            }
