from mock import MagicMock

from django.test import TestCase

from haupt.orchestration.scheduler.resolver import SchedulingResolver
from polyaxon._constants.metadata import (
    META_CONCURRENCY,
    META_HAS_EARLY_STOPPING,
    META_IS_EXTERNAL,
    META_PORTS,
    META_REWRITE_PATH,
    META_TMUX,
    META_TTL,
)
from polyaxon.schemas import (
    V1CompiledOperation,
    V1Dag,
    V1Job,
    V1Mapping,
    V1Plugins,
    V1RunKind,
    V1Service,
    V1Termination,
)


class TestPersistMetaInfo(TestCase):
    @staticmethod
    def _make_resolver(run, compiled_operation):
        resolver = MagicMock(spec=SchedulingResolver)
        resolver.run = run
        resolver.compiled_operation = compiled_operation
        return resolver

    @staticmethod
    def _make_run(kind=V1RunKind.JOB):
        run = MagicMock()
        run.meta_info = {}
        run.is_matrix = kind == V1RunKind.MATRIX
        run.is_dag = kind == V1RunKind.DAG
        return run

    def test_matrix_concurrency_sets_meta(self):
        run = self._make_run(kind=V1RunKind.MATRIX)
        op = V1CompiledOperation.model_construct(
            matrix=V1Mapping.model_construct(
                kind="mapping",
                values=[{"a": 1}],
                concurrency=4,
            ),
            run=V1Job.model_construct(kind=V1RunKind.JOB),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert run.meta_info[META_CONCURRENCY] == 4

    def test_dag_concurrency_sets_meta(self):
        run = self._make_run(kind=V1RunKind.DAG)
        op = V1CompiledOperation.model_construct(
            run=V1Dag.model_construct(kind=V1RunKind.DAG, concurrency=3),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert run.meta_info[META_CONCURRENCY] == 3

    def test_matrix_without_concurrency_skips_meta(self):
        run = self._make_run(kind=V1RunKind.MATRIX)
        op = V1CompiledOperation.model_construct(
            matrix=V1Mapping.model_construct(
                kind="mapping", values=[{"a": 1}], concurrency=None
            ),
            run=V1Job.model_construct(kind=V1RunKind.JOB),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert META_CONCURRENCY not in run.meta_info

    def test_job_kind_does_not_set_concurrency(self):
        run = self._make_run(kind=V1RunKind.JOB)
        op = V1CompiledOperation.model_construct(
            run=V1Job.model_construct(kind=V1RunKind.JOB),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert META_CONCURRENCY not in run.meta_info

    def test_matrix_early_stopping_sets_meta(self):
        run = self._make_run(kind=V1RunKind.MATRIX)
        op = V1CompiledOperation.model_construct(
            matrix=V1Mapping.model_construct(
                kind="mapping",
                values=[{"a": 1}],
                early_stopping=[{"kind": "metric_early_stopping"}],
            ),
            run=V1Job.model_construct(kind=V1RunKind.JOB),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert run.meta_info[META_HAS_EARLY_STOPPING] is True

    def test_dag_early_stopping_sets_meta(self):
        run = self._make_run(kind=V1RunKind.DAG)
        op = V1CompiledOperation.model_construct(
            run=V1Dag.model_construct(
                kind=V1RunKind.DAG,
                early_stopping=[{"kind": "metric_early_stopping"}],
            ),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert run.meta_info[META_HAS_EARLY_STOPPING] is True

    def test_no_early_stopping_skips_meta(self):
        run = self._make_run(kind=V1RunKind.MATRIX)
        op = V1CompiledOperation.model_construct(
            matrix=V1Mapping.model_construct(
                kind="mapping", values=[{"a": 1}], early_stopping=None
            ),
            run=V1Job.model_construct(kind=V1RunKind.JOB),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert META_HAS_EARLY_STOPPING not in run.meta_info

    def test_service_rewrite_path_sets_meta(self):
        run = self._make_run(kind=V1RunKind.SERVICE)
        op = V1CompiledOperation.model_construct(
            run=V1Service.model_construct(kind=V1RunKind.SERVICE, rewrite_path=True),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert run.meta_info[META_REWRITE_PATH] is True

    def test_service_rewrite_path_false_skips_meta(self):
        run = self._make_run(kind=V1RunKind.SERVICE)
        op = V1CompiledOperation.model_construct(
            run=V1Service.model_construct(kind=V1RunKind.SERVICE, rewrite_path=False),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert META_REWRITE_PATH not in run.meta_info

    def test_service_is_external_sets_meta(self):
        run = self._make_run(kind=V1RunKind.SERVICE)
        op = V1CompiledOperation.model_construct(
            run=V1Service.model_construct(kind=V1RunKind.SERVICE, is_external=True),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert run.meta_info[META_IS_EXTERNAL] is True

    def test_service_ports_sets_meta(self):
        run = self._make_run(kind=V1RunKind.SERVICE)
        op = V1CompiledOperation.model_construct(
            run=V1Service.model_construct(kind=V1RunKind.SERVICE, ports=[8000, 8080]),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert run.meta_info[META_PORTS] == [8000, 8080]

    def test_non_service_ignores_service_flags(self):
        run = self._make_run(kind=V1RunKind.JOB)
        op = V1CompiledOperation.model_construct(
            run=V1Job.model_construct(kind=V1RunKind.JOB),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert META_REWRITE_PATH not in run.meta_info
        assert META_IS_EXTERNAL not in run.meta_info
        assert META_PORTS not in run.meta_info

    def test_termination_ttl_sets_meta(self):
        run = self._make_run(kind=V1RunKind.JOB)
        op = V1CompiledOperation.model_construct(
            run=V1Job.model_construct(kind=V1RunKind.JOB),
            termination=V1Termination.model_construct(ttl=3600),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert run.meta_info[META_TTL] == 3600

    def test_termination_without_ttl_skips_meta(self):
        run = self._make_run(kind=V1RunKind.JOB)
        op = V1CompiledOperation.model_construct(
            run=V1Job.model_construct(kind=V1RunKind.JOB),
            termination=V1Termination.model_construct(ttl=None),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert META_TTL not in run.meta_info

    def test_no_termination_skips_ttl(self):
        run = self._make_run(kind=V1RunKind.JOB)
        op = V1CompiledOperation.model_construct(
            run=V1Job.model_construct(kind=V1RunKind.JOB),
            termination=None,
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert META_TTL not in run.meta_info

    def test_plugins_tmux_sets_meta(self):
        run = self._make_run(kind=V1RunKind.JOB)
        op = V1CompiledOperation.model_construct(
            run=V1Job.model_construct(kind=V1RunKind.JOB),
            plugins=V1Plugins.model_construct(tmux=True),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert run.meta_info[META_TMUX] is True

    def test_plugins_tmux_false_skips_meta(self):
        run = self._make_run(kind=V1RunKind.JOB)
        op = V1CompiledOperation.model_construct(
            run=V1Job.model_construct(kind=V1RunKind.JOB),
            plugins=V1Plugins.model_construct(tmux=False),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert META_TMUX not in run.meta_info

    def test_no_plugins_skips_tmux(self):
        run = self._make_run(kind=V1RunKind.JOB)
        op = V1CompiledOperation.model_construct(
            run=V1Job.model_construct(kind=V1RunKind.JOB),
            plugins=None,
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert META_TMUX not in run.meta_info

    def test_all_flags_combined(self):
        run = self._make_run(kind=V1RunKind.MATRIX)
        op = V1CompiledOperation.model_construct(
            matrix=V1Mapping.model_construct(
                kind="mapping",
                values=[{"a": 1}],
                concurrency=2,
                early_stopping=[{"kind": "metric_early_stopping"}],
            ),
            run=V1Job.model_construct(kind=V1RunKind.JOB),
            termination=V1Termination.model_construct(ttl=120),
            plugins=V1Plugins.model_construct(tmux=True),
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert run.meta_info == {
            META_CONCURRENCY: 2,
            META_HAS_EARLY_STOPPING: True,
            META_TTL: 120,
            META_TMUX: True,
        }

    def test_empty_compiled_operation(self):
        run = self._make_run(kind=V1RunKind.JOB)
        op = V1CompiledOperation.model_construct(
            run=V1Job.model_construct(kind=V1RunKind.JOB),
            termination=None,
            plugins=None,
        )
        SchedulingResolver._persist_meta_info(self._make_resolver(run, op))
        assert run.meta_info == {}
