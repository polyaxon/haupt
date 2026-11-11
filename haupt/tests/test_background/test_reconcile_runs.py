from datetime import timedelta
from mock import patch
import pytest

from django.utils.timezone import now

from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.db.defs import Models
from haupt.db.factories.runs import RunFactory
from haupt.db.managers.artifacts import atomic_set_artifacts
from haupt.orchestration import operations
from haupt.orchestration.scheduler.manager import SchedulingManager
from polyaxon.schemas import (
    ManagedBy,
    V1ArtifactKind,
    V1CloningKind,
    V1MatrixKind,
    V1RunArtifact,
    V1RunEdgeKind,
    V1RunKind,
    V1RunPending,
    V1Statuses,
)
from tests.test_background.case import BaseTest


PREPARE = SchedulerCeleryTasks.RUNS_PREPARE
START = SchedulerCeleryTasks.RUNS_START
BUILT = SchedulerCeleryTasks.RUNS_BUILT
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

    def _clone(self, original, **kwargs):
        # Managed clones need a compiled specification (`run_created` signal)
        return self._run(
            original=original,
            cloning_kind=V1CloningKind.CACHE,
            pending=V1RunPending.CACHE,
            content="test",
            **kwargs,
        )

    @staticmethod
    def _age(*runs):
        Models.Run.objects.filter(id__in=[r.id for r in runs]).update(
            updated_at=now() - timedelta(minutes=10)
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
    def test_trigger_skips_dependent_pipeline_with_children(self, trigger):
        dag = self._run(kind=V1RunKind.DAG, status=V1Statuses.RUNNING)
        upstream = self._run(pipeline=dag, status=V1Statuses.SUCCEEDED)
        nested = self._run(pipeline=dag, kind=V1RunKind.DAG)
        nested_child = self._run(pipeline=nested)
        self._dag_edge(upstream, nested)
        self._age(dag, upstream, nested, nested_child)
        with self.assertLogs("polyaxon.scheduler", level="WARNING"):
            assert self._reconcile() == []
        assert trigger.call_count == 0

    @patch.object(SchedulingManager, "_trigger_downstream")
    def test_prepare_built_child(self, trigger):
        dag = self._run(kind=V1RunKind.DAG, status=V1Statuses.RUNNING)
        upstream = self._run(pipeline=dag, status=V1Statuses.SUCCEEDED)
        builder = self._run(runtime=V1RunKind.BUILDER, status=V1Statuses.SUCCEEDED)
        child = self._run(pipeline=dag)
        # `runs_built` does not stagger prepares, a busy sibling does not delay it
        self._run(pipeline=dag, status=V1Statuses.RUNNING)
        self._dag_edge(upstream, child)
        self._build_edge(builder, child)
        self._age(dag, upstream, builder, child)
        assert self._reconcile() == [(PREPARE, child.id)]
        assert trigger.call_count == 0

    def test_prepare_iteration_child_once_matrix_is_quiet(self):
        bayes = self._run(
            kind=V1RunKind.MATRIX,
            runtime=V1MatrixKind.BAYES,
            status=V1Statuses.RUNNING,
        )
        tuner = self._run(
            pipeline=bayes, kind=V1RunKind.TUNER, status=V1Statuses.SUCCEEDED
        )
        child = self._run(pipeline=bayes)
        # `runs_iterate` links the finished tuner to each iteration child
        Models.RunEdge.objects.create(
            upstream=tuner, downstream=child, kind=V1RunEdgeKind.JOIN
        )
        self._age(bayes, child)
        # The tuner just finished, its trigger may still be pending
        assert self._reconcile() == []

        self._age(tuner)
        assert self._reconcile() == [(PREPARE, child.id)]

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

    def test_notify_build_only_for_claimed_runs(self):
        builder = self._run(runtime=V1RunKind.BUILDER, status=V1Statuses.SUCCEEDED)
        artifact = V1RunArtifact(
            name="destination",
            state=builder.uuid,
            kind=V1ArtifactKind.DOCKER_IMAGE,
            summary=dict(image="foo/bar"),
            is_input=False,
        )
        atomic_set_artifacts(run=builder, artifacts=[artifact])
        first = self._run(pending=V1RunPending.BUILD)
        second = self._run(pending=V1RunPending.BUILD)
        self._build_edge(builder, first)
        self._build_edge(builder, second)
        self._age(first, second)
        # Builder finished recently, its notification may still be pending
        assert self._reconcile() == []

        self._age(builder)
        # Both runs wait on the same builder, each sweep releases only its claimed run
        first_sweep = self._reconcile(limit=1)
        second_sweep = self._reconcile(limit=1)
        assert len(first_sweep) == len(second_sweep) == 1
        assert {first_sweep[0], second_sweep[0]} == {
            (BUILT, first.id),
            (BUILT, second.id),
        }

    def test_notify_cache_skips_done_clones(self):
        stopped_original = self._run(status=V1Statuses.SUCCEEDED)
        stopped_clone = self._clone(stopped_original, status=V1Statuses.STOPPED)
        original = self._run(status=V1Statuses.FAILED)
        clone = self._clone(original)
        self._age(stopped_original, stopped_clone, original, clone)
        # Releasing a clone records auditor events, check the database not the sends
        SchedulingManager.reconcile_runs(limit=1)
        stopped_clone.refresh_from_db()
        clone.refresh_from_db()
        assert stopped_clone.pending == V1RunPending.CACHE
        assert clone.status == V1Statuses.FAILED
        assert clone.pending is None

    def test_notify_cache_only_for_claimed_runs(self):
        original = self._run(status=V1Statuses.SUCCEEDED)
        first = self._clone(original)
        second = self._clone(original)
        self._age(original, first, second)
        clones = Models.Run.objects.filter(id__in=[first.id, second.id])
        # Both clones wait on the same original, each sweep releases only its claimed clone
        SchedulingManager.reconcile_runs(limit=1)
        assert clones.filter(pending=V1RunPending.CACHE).count() == 1

        SchedulingManager.reconcile_runs(limit=1)
        assert set(clones.values_list("status", "pending")) == {
            (V1Statuses.SUCCEEDED, None)
        }

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
        self._age(first, second)
        self.send.side_effect = [Exception("boom"), None]
        with self.assertLogs("polyaxon.scheduler", level="ERROR"):
            assert set(self._reconcile()) == {
                (PREPARE, first.id),
                (PREPARE, second.id),
            }
