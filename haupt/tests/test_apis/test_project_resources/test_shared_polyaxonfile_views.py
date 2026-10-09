from copy import deepcopy
from datetime import timedelta
import pytest
from unittest.mock import patch

from rest_framework import status

from clipped.utils.json import orjson_dumps, orjson_loads
from clipped.utils.tz import now
from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.managers.statuses import new_run_status
from haupt.db.managers.versions import get_component_version_state
from haupt.db.models.project_versions import ProjectVersion
from haupt.db.models.run_edges import RunEdge
from haupt.db.models.runs import Run
from haupt.orchestration.scheduler.manager import SchedulingManager
from polyaxon import settings as polyaxon_settings
from polyaxon._connections import V1BucketConnection, V1Connection, V1ConnectionKind
from polyaxon._flow.polyaxonfile import V1Polyaxonfile
from polyaxon._polyaxonfile import CompiledOperationSpecification
from polyaxon._polyaxonfile.specs import read_polyaxonfile
from polyaxon._schemas.agent import AgentConfig
from polyaxon.api import API_V1
from polyaxon.schemas import V1RunKind, V1StatusCondition, V1Statuses
from tests.base.case import BaseTest


@pytest.mark.projects_resources_mark
class TestSharedPolyaxonfileViews(BaseTest):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()
        self.url = f"/{API_V1}/polyaxon/{self.project.name}/runs/"
        self.version_url = f"/{API_V1}/polyaxon/{self.project.name}/versions/component"
        self.agent_config = AgentConfig(
            namespace="foo",
            artifacts_store=V1Connection(
                name="moo",
                kind=V1ConnectionKind.GCS,
                schema_=V1BucketConnection(bucket="gs//:foo"),
            ),
        )

    def test_shared_schedules_create_first_next_and_restarted_runs(self):
        start_at = (now() + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        for kind, runtime in (
            (None, V1RunKind.JOB),
            ("component", V1RunKind.JOB),
            ("operation", V1RunKind.SERVICE),
            ("embedded", V1RunKind.JOB),
        ):
            with self.subTest(kind=kind, runtime=runtime):
                source = {
                    "strictParams": True,
                    "cache": {"disable": True},
                    "inputs": [{"name": "count", "type": "int"}],
                    "outputs": [{"name": "result", "type": "str", "value": "done"}],
                    "params": {
                        "count": 3,
                        "run_id": {
                            "value": "{{ globals.uuid }}",
                            "contextOnly": True,
                            "toEnv": "RUN_ID",
                        },
                    },
                    "schedule": {
                        "kind": "cron",
                        "cron": "0 0 * * *",
                        "startAt": start_at.isoformat(),
                        "maxRuns": 2,
                    },
                    "run": {
                        "kind": runtime,
                        "container": {
                            "image": "busybox:1.36",
                            "command": ["sh", "-c"],
                            "args": ["echo {{ count }} {{ run_id }}"],
                            "resources": {"limits": {"nvidia.com/gpu": 1}},
                        },
                    },
                }
                if runtime == V1RunKind.SERVICE:
                    source["run"]["ports"] = [8080]
                if kind == "embedded":
                    source = {
                        "kind": "operation",
                        "component": {"kind": "component", **source},
                    }
                elif kind:
                    source["kind"] = kind
                response = self.client.post(self.url, {"content": orjson_dumps(source)})
                assert response.status_code == status.HTTP_201_CREATED, response.data
                run = Run.objects.get(uuid=response.data["uuid"])
                raw_content = run.raw_content
                assert run.kind == V1RunKind.SCHEDULE

                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=run.id, start=False)

                run.refresh_from_db()
                assert run.status == V1Statuses.COMPILED, run.status_conditions
                parent_content = run.content
                parent = CompiledOperationSpecification.read(parent_content)
                assert parent.strict_params is True
                assert parent.contexts[0].value == run.uuid.hex
                assert run.pipeline_runs.count() == 1
                first = run.pipeline_runs.get()
                for index in range(2):
                    if index:
                        SchedulingManager._start_schedule_based_on_run(
                            first, depends_on_past=False
                        )
                    assert run.pipeline_runs.count() == index + 1
                    child = run.pipeline_runs.order_by("schedule_at").last()
                    child_raw_content = child.raw_content
                    child_source = read_polyaxonfile(child_raw_content)
                    layer = child_source.component or child_source
                    assert child.schedule_at == start_at + timedelta(days=index)
                    assert child.kind == runtime
                    assert child.pipeline_id == run.id
                    assert child.component_state == run.component_state
                    assert child_source.kind == (
                        "operation" if kind == "embedded" else kind
                    )
                    assert child_source.schedule is None
                    assert layer.schedule is None
                    assert layer.params["run_id"].value == "{{ globals.uuid }}"
                    compiled = CompiledOperationSpecification.read(child.content)
                    assert compiled.schedule is None
                    assert compiled.strict_params is True
                    assert compiled.run == parent.run

                    with patch.object(
                        polyaxon_settings, "AGENT_CONFIG", self.agent_config
                    ):
                        SchedulingManager.runs_prepare(run_id=child.id, start=False)

                    child.refresh_from_db()
                    assert child.status == V1Statuses.COMPILED, child.status_conditions
                    assert child.raw_content == child_raw_content
                    assert child.inputs == {"count": 3, "run_id": child.uuid.hex}
                    assert child.outputs == {"result": "done"}
                    assert not child.pipeline_runs.exists()
                    compiled = CompiledOperationSpecification.read(child.content)
                    assert compiled.strict_params is None
                    assert compiled.contexts[0].to_env == "RUN_ID"
                    assert compiled.run.container.args == [f"echo 3 {child.uuid.hex}"]
                    assert (
                        compiled.run.container.resources["limits"]["nvidia.com/gpu"]
                        == 1
                    )
                    if runtime == V1RunKind.SERVICE:
                        assert compiled.run.ports == [8080]

                with patch("haupt.common.workers.send"):
                    response = self.client.post(
                        f"{self.url}{first.uuid.hex}/restart/", {}
                    )
                assert response.status_code == status.HTTP_201_CREATED, response.data
                restarted = Run.objects.get(uuid=response.data["uuid"])
                assert restarted.original_id == first.id
                assert restarted.pipeline_id is None
                assert restarted.kind == runtime

                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=restarted.id, start=False)

                restarted.refresh_from_db()
                assert restarted.status == V1Statuses.COMPILED, (
                    restarted.status_conditions
                )
                assert restarted.inputs == {"count": 3, "run_id": restarted.uuid.hex}
                assert not restarted.pipeline_runs.exists()
                compiled = CompiledOperationSpecification.read(restarted.content)
                assert compiled.schedule is None
                assert compiled.run.container.args == [f"echo 3 {restarted.uuid.hex}"]

                SchedulingManager._start_schedule_based_on_run(
                    child, depends_on_past=False
                )
                run.refresh_from_db()
                assert run.status == V1Statuses.SUCCEEDED
                assert run.pipeline_runs.count() == 2
                assert run.raw_content == raw_content
                assert run.content == parent_content

    def test_shared_schedule_keeps_inherited_matrix_and_approval(self):
        start_at = (now() + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        source = {
            "kind": "component",
            "strictParams": True,
            "isApproved": True,
            "cache": {"disable": True},
            "inputs": [{"name": "count", "type": "int"}],
            "params": {
                "count": 0,
                "message": {
                    "value": "hello",
                    "contextOnly": True,
                    "toEnv": "MESSAGE",
                },
            },
            "schedule": {
                "kind": "cron",
                "cron": "0 0 * * *",
                "startAt": start_at.isoformat(),
                "maxRuns": 2,
            },
            "matrix": {
                "kind": "grid",
                "params": {"count": {"kind": "choice", "value": [1, 2]}},
            },
            "run": {
                "kind": "job",
                "container": {
                    "image": "busybox:1.36",
                    "command": ["sh", "-c"],
                    "args": ["echo {{ count }} {{ message }}"],
                    "resources": {"limits": {"nvidia.com/gpu": 1}},
                },
            },
        }
        source = {"kind": "operation", "component": source}
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        raw_content = run.raw_content
        assert run.kind == V1RunKind.SCHEDULE

        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=run.id, start=False)

        run.refresh_from_db()
        assert run.status == V1Statuses.COMPILED, run.status_conditions
        parent_content = run.content
        parent = CompiledOperationSpecification.read(parent_content)
        assert parent.matrix.kind == "grid"
        assert run.pipeline_runs.count() == 1
        first = run.pipeline_runs.get()
        for index in range(2):
            if index:
                SchedulingManager._start_schedule_based_on_run(
                    first, depends_on_past=False
                )
            assert run.pipeline_runs.count() == index + 1
            occurrence = run.pipeline_runs.order_by("schedule_at").last()
            occurrence_raw = occurrence.raw_content
            assert occurrence.kind == V1RunKind.MATRIX
            assert occurrence.schedule_at == start_at + timedelta(days=index)
            assert occurrence.component_state == run.component_state
            source = read_polyaxonfile(occurrence_raw)
            assert source.schedule is None
            assert source.component.schedule is None
            assert source.component.matrix.kind == "grid"
            assert source.component.is_approved is True
            compiled = CompiledOperationSpecification.read(occurrence.content)
            assert compiled.schedule is None
            assert compiled.strict_params is True
            assert compiled.is_approved is True
            assert compiled.run == parent.run

            with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                SchedulingManager.runs_prepare(run_id=occurrence.id, start=False)

            occurrence.refresh_from_db()
            assert occurrence.status == V1Statuses.COMPILED, (
                occurrence.status_conditions
            )
            assert occurrence.raw_content == occurrence_raw
            jobs = list(occurrence.pipeline_runs.order_by("id"))
            assert len(jobs) == 2
            assert {job.inputs["count"] for job in jobs} == {1, 2}
            for job in jobs:
                count = job.inputs["count"]
                job_source = read_polyaxonfile(job.raw_content)
                assert job.kind == V1RunKind.JOB
                assert job_source.schedule is None
                assert job_source.matrix is None
                assert job_source.is_approved is None
                assert job_source.component.schedule is None
                assert job_source.component.matrix is None
                assert job_source.component.is_approved is None
                assert job_source.params["message"].context_only is True
                assert job_source.params["message"].to_env == "MESSAGE"
                compiled = CompiledOperationSpecification.read(job.content)
                assert compiled.strict_params is True

                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=job.id, start=False)

                job.refresh_from_db()
                assert job.status == V1Statuses.COMPILED, job.status_conditions
                assert job.inputs == {"count": count, "message": "hello"}
                assert not job.pipeline_runs.exists()
                compiled = CompiledOperationSpecification.read(job.content)
                assert compiled.schedule is None
                assert compiled.matrix is None
                assert compiled.strict_params is None
                assert compiled.run.container.image == "busybox:1.36"
                assert compiled.run.container.args == [f"echo {count} hello"]
                assert compiled.run.container.resources["limits"]["nvidia.com/gpu"] == 1
            run.refresh_from_db()
            assert run.raw_content == raw_content
            assert run.content == parent_content

    def test_shared_schedule_creates_dags_with_children_and_edges(self):
        start_at = (now() + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        source = {
            "kind": "operation",
            "strictParams": True,
            "cache": {"disable": True},
            "inputs": [{"name": "count", "type": "int"}],
            "params": {"count": 3},
            "schedule": {
                "kind": "cron",
                "cron": "0 0 * * *",
                "startAt": start_at.isoformat(),
                "maxRuns": 2,
            },
            "run": {
                "kind": "dag",
                "components": [
                    {
                        "name": "echo",
                        "inputs": [{"name": "count", "type": "int"}],
                        "params": {"count": {"ref": "dag", "value": "inputs.count"}},
                        "schedule": {"kind": "interval", "frequency": 120},
                        "run": {
                            "kind": "job",
                            "container": {
                                "image": "busybox:1.36",
                                "command": ["sh", "-c"],
                                "args": ["echo {{ count }}"],
                                "resources": {"limits": {"nvidia.com/gpu": 1}},
                            },
                        },
                    }
                ],
                "operations": [
                    {"name": "first", "dagRef": "echo"},
                    {
                        "name": "second",
                        "dagRef": "echo",
                        "dependencies": ["first"],
                        "conditions": "true",
                        "trigger": "all_succeeded",
                        "skipOnUpstreamSkip": False,
                    },
                ],
            },
        }
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        raw_content = run.raw_content
        assert run.kind == V1RunKind.SCHEDULE

        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=run.id, start=False)

        run.refresh_from_db()
        assert run.status == V1Statuses.COMPILED, run.status_conditions
        parent_content = run.content
        assert run.pipeline_runs.count() == 1
        first = run.pipeline_runs.get()
        for index in range(2):
            if index:
                SchedulingManager._start_schedule_based_on_run(
                    first, depends_on_past=False
                )
            assert run.pipeline_runs.count() == index + 1
            dag = run.pipeline_runs.order_by("schedule_at").last()
            dag_raw = dag.raw_content
            assert dag.kind == V1RunKind.DAG
            assert dag.schedule_at == start_at + timedelta(days=index)
            assert dag.component_state == run.component_state
            source = read_polyaxonfile(dag_raw)
            assert source.schedule is None
            assert source.run.components[0].schedule.frequency == timedelta(seconds=120)

            with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                SchedulingManager.runs_prepare(run_id=dag.id, start=False)

            dag.refresh_from_db()
            assert dag.status == V1Statuses.COMPILED, dag.status_conditions
            assert dag.raw_content == dag_raw
            assert dag.inputs == {"count": 3}
            children = {child.name: child for child in dag.pipeline_runs.all()}
            assert set(children) == {"first", "second"}
            assert RunEdge.objects.filter(downstream__pipeline=dag).count() == 1
            edge = RunEdge.objects.get(
                upstream=children["first"], downstream=children["second"]
            )
            assert edge.kind == "dag"
            assert edge.statuses == []
            compiled = CompiledOperationSpecification.read(children["second"].content)
            assert compiled.dependencies == ["first"]
            assert compiled.conditions == "true"
            assert compiled.trigger == "all_succeeded"
            assert compiled.skip_on_upstream_skip is False

            for name in ("first", "second"):
                child = children[name]
                assert child.kind == V1RunKind.JOB
                assert child.pipeline_id == dag.id
                assert child.controller_id == dag.id
                assert child.params["count"] == {"value": 3}

                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=child.id, start=False)

                child.refresh_from_db()
                assert child.status == V1Statuses.COMPILED, child.status_conditions
                assert child.inputs == {"count": 3}
                assert not child.pipeline_runs.exists()
                compiled = CompiledOperationSpecification.read(child.content)
                assert compiled.schedule is None
                assert compiled.run.container.args == ["echo 3"]
                assert compiled.run.container.resources["limits"]["nvidia.com/gpu"] == 1
                if name == "first":
                    child.status = V1Statuses.SUCCEEDED
                    child.save(update_fields=["status"])
                    with patch("haupt.common.workers.send") as workers_send:
                        SchedulingManager.runs_notify_done(run_id=child.id)
                    assert {
                        call.kwargs["kwargs"]["run_id"]
                        for call in workers_send.call_args_list
                        if call.args[0] == SchedulerCeleryTasks.RUNS_PREPARE
                    } == {children["second"].id}
            run.refresh_from_db()
            assert run.raw_content == raw_content
            assert run.content == parent_content

    def test_shared_grid_jobs_and_services_through_prepare_and_restart(self):
        for runtime in (V1RunKind.JOB, V1RunKind.SERVICE):
            for kind in (None, "component", "operation", "embedded"):
                with self.subTest(runtime=runtime, kind=kind):
                    source = {
                        "strictParams": True,
                        "cache": {"disable": True},
                        "inputs": [
                            {"name": "count", "type": "int"},
                            {"name": "rate", "type": "float"},
                        ],
                        "outputs": [{"name": "result", "type": "str", "value": "done"}],
                        "params": {
                            "count": {"value": 0, "contextOnly": False},
                            "rate": 0.5,
                            "message": {
                                "value": "hello",
                                "contextOnly": True,
                                "toEnv": "MESSAGE",
                            },
                        },
                        "matrix": {
                            "kind": "grid",
                            "params": {"count": {"kind": "choice", "value": [1, 2]}},
                        },
                        "run": {
                            "kind": runtime,
                            "container": {
                                "image": "busybox:1.36",
                                "command": ["sh", "-c"],
                                "args": ["echo {{ count }} {{ rate }} {{ message }}"],
                                "resources": {"limits": {"nvidia.com/gpu": 1}},
                            },
                        },
                    }
                    if runtime == V1RunKind.SERVICE:
                        source["run"]["ports"] = [8080]
                    if kind == "embedded":
                        source = {
                            "kind": "operation",
                            "strictParams": False,
                            "component": {"kind": "component", **source},
                        }
                    elif kind:
                        source["kind"] = kind
                    response = self.client.post(
                        self.url, {"content": orjson_dumps(source)}
                    )
                    assert response.status_code == status.HTTP_201_CREATED, (
                        response.data
                    )
                    run = Run.objects.get(uuid=response.data["uuid"])
                    raw_content = run.raw_content
                    assert run.is_matrix
                    assert run.runtime == "grid"

                    with patch.object(
                        polyaxon_settings, "AGENT_CONFIG", self.agent_config
                    ):
                        SchedulingManager.runs_prepare(run_id=run.id, start=False)

                    run.refresh_from_db()
                    assert run.status == V1Statuses.COMPILED, run.status_conditions
                    assert run.raw_content == raw_content
                    parent = CompiledOperationSpecification.read(run.content)
                    assert parent.strict_params is True
                    children = list(run.pipeline_runs.order_by("id"))
                    assert len(children) == 2
                    assert not RunEdge.objects.filter(downstream__pipeline=run).exists()
                    for count, child in enumerate(children, 1):
                        child_raw_content = child.raw_content
                        child_source = read_polyaxonfile(child_raw_content)
                        compiled = CompiledOperationSpecification.read(child.content)
                        assert child.kind == runtime
                        assert child.pipeline_id == run.id
                        assert child.controller_id == run.id
                        assert child_source.kind == (
                            "operation" if kind == "embedded" else kind
                        )
                        assert child_source.matrix is None
                        if child_source.component is not None:
                            assert child_source.component.matrix is None
                        assert child_source.strict_params is True
                        assert child_source.params["count"].context_only is False
                        assert child_source.params["message"].context_only is True
                        assert child_source.params["message"].to_env == "MESSAGE"
                        assert child.inputs == {"count": count, "message": "hello"}
                        assert child.component_state == get_component_version_state(
                            child_source.component or child_source
                        )
                        assert compiled.matrix is None
                        assert compiled.strict_params is True
                        assert compiled.run == parent.run
                        assert compiled.inputs == parent.inputs
                        assert compiled.outputs == parent.outputs

                        with patch.object(
                            polyaxon_settings, "AGENT_CONFIG", self.agent_config
                        ):
                            SchedulingManager.runs_prepare(run_id=child.id, start=False)

                        child.refresh_from_db()
                        assert child.status == V1Statuses.COMPILED, (
                            child.status_conditions
                        )
                        assert child.raw_content == child_raw_content
                        assert child.inputs == {
                            "count": count,
                            "rate": 0.5,
                            "message": "hello",
                        }
                        assert child.outputs == {"result": "done"}
                        compiled = CompiledOperationSpecification.read(child.content)
                        assert compiled.strict_params is None
                        assert {io.name: io.value for io in compiled.inputs} == {
                            "count": count,
                            "rate": 0.5,
                        }
                        assert {io.name: io.value for io in compiled.contexts} == {
                            "message": "hello"
                        }
                        assert compiled.contexts[0].to_env == "MESSAGE"
                        assert compiled.run.container.args == [
                            f"echo {count} 0.5 hello"
                        ]
                        assert (
                            compiled.run.container.resources["limits"]["nvidia.com/gpu"]
                            == 1
                        )
                        if runtime == V1RunKind.SERVICE:
                            assert compiled.run.ports == [8080]
                    assert len({child.component_state for child in children}) == (
                        1 if kind == "embedded" else 2
                    )

                    child = children[0]
                    with patch("haupt.common.workers.send"):
                        response = self.client.post(
                            f"{self.url}{child.uuid.hex}/restart/", {}
                        )
                    assert response.status_code == status.HTTP_201_CREATED, (
                        response.data
                    )
                    restarted = Run.objects.get(uuid=response.data["uuid"])
                    assert restarted.original_id == child.id
                    assert restarted.pipeline_id is None

                    with patch.object(
                        polyaxon_settings, "AGENT_CONFIG", self.agent_config
                    ):
                        SchedulingManager.runs_prepare(run_id=restarted.id, start=False)

                    restarted.refresh_from_db()
                    assert restarted.status == V1Statuses.COMPILED, (
                        restarted.status_conditions
                    )
                    assert restarted.inputs == child.inputs
                    assert not restarted.pipeline_runs.exists()
                    compiled = CompiledOperationSpecification.read(restarted.content)
                    assert compiled.matrix is None
                    assert compiled.run.container.args == ["echo 1 0.5 hello"]

    @patch("haupt.common.workers.send")
    def test_shared_matrix_later_suggestions_through_prepare(self, worker_send):
        source = {
            "kind": "component",
            "strictParams": True,
            "cache": {"disable": True},
            "params": {
                "count": {"value": 0, "contextOnly": True, "toEnv": "COUNT"},
                "message": {"value": "hello", "contextOnly": True},
            },
            "matrix": {
                "kind": "bayes",
                "numInitialRuns": 2,
                "maxIterations": 2,
                "metric": {"name": "loss", "optimization": "minimize"},
                "params": {"count": {"kind": "choice", "value": [1, 2, 3]}},
            },
            "run": {
                "kind": "job",
                "container": {
                    "image": "busybox:1.36",
                    "command": ["sh", "-c"],
                    "args": ["echo {{ count }} {{ message }}"],
                    "resources": {"limits": {"nvidia.com/gpu": 1}},
                },
            },
        }
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        raw_content = run.raw_content
        assert run.is_matrix
        assert run.runtime == "bayes"

        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=run.id, start=False)

        run.refresh_from_db()
        assert run.status == V1Statuses.COMPILED, run.status_conditions
        assert not run.pipeline_runs.exists()
        worker_send.assert_any_call(
            SchedulerCeleryTasks.RUNS_TUNE,
            kwargs={"run_id": run.id},
            eager_kwargs={"run": run},
        )
        parent_content = run.content
        parent = CompiledOperationSpecification.read(parent_content)
        assert parent.strict_params is True
        assert parent.inputs is None
        previous_children = {}
        for iteration, counts in ((1, [1, 2]), (2, [3])):
            tuner = RunFactory(
                project=self.project,
                user=run.user,
                pipeline=run,
                controller=run,
                kind=V1RunKind.JOB,
                runtime=V1RunKind.TUNER,
                status=V1Statuses.SUCCEEDED,
                inputs={"iteration": iteration},
                outputs={"suggestions": [{"count": count} for count in counts]},
            )

            SchedulingManager.runs_iterate(run_id=tuner.id)

            run.refresh_from_db()
            assert run.meta_info["iteration"] == iteration
            assert run.raw_content == raw_content
            assert run.content == parent_content
            children = [
                child
                for child in run.pipeline_runs.order_by("id")
                if child.meta_info.get("iteration") == iteration
            ]
            assert len(children) == len(counts)
            for count, child in zip(counts, children):
                child_raw_content = child.raw_content
                child_source = read_polyaxonfile(child_raw_content)
                compiled = CompiledOperationSpecification.read(child.content)
                assert child.is_job
                assert child.pipeline_id == run.id
                assert child.controller_id == run.id
                assert child_source.matrix is None
                assert child_source.strict_params is True
                assert child_source.params["count"].context_only is True
                assert child_source.params["count"].to_env == "COUNT"
                assert child.inputs == {"count": count, "message": "hello"}
                assert child.component_state == get_component_version_state(
                    child_source.component or child_source
                )
                assert compiled.matrix is None
                assert compiled.inputs is None
                assert compiled.strict_params is True
                assert compiled.run == parent.run
                edge = RunEdge.objects.get(downstream=child)
                assert edge.upstream_id == tuner.id
                assert edge.kind == "join"

                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=child.id, start=False)

                child.refresh_from_db()
                assert child.status == V1Statuses.COMPILED, child.status_conditions
                assert child.raw_content == child_raw_content
                assert child.inputs == {"count": count, "message": "hello"}
                compiled = CompiledOperationSpecification.read(child.content)
                assert compiled.strict_params is None
                assert compiled.inputs is None
                assert {io.name: io.value for io in compiled.contexts} == {
                    "count": count,
                    "message": "hello",
                }
                assert compiled.run.container.image == "busybox:1.36"
                assert compiled.run.container.args == [f"echo {count} hello"]
                assert compiled.run.container.resources["limits"]["nvidia.com/gpu"] == 1
            for child_id, (saved_raw, saved_content) in previous_children.items():
                previous = Run.objects.get(id=child_id)
                assert previous.raw_content == saved_raw
                assert previous.content == saved_content
            previous_children.update(
                {child.id: (child.raw_content, child.content) for child in children}
            )
        assert run.pipeline_runs.exclude(runtime=V1RunKind.TUNER).count() == 3
        assert RunEdge.objects.filter(downstream__pipeline=run).count() == 3

    def test_shared_matrix_dag_children_pass_suggestions_to_jobs(self):
        source = {
            "kind": "operation",
            "cache": {"disable": True},
            "strictParams": True,
            "inputs": [{"name": "count", "type": "int"}],
            "matrix": {
                "kind": "grid",
                "params": {"count": {"kind": "choice", "value": [1, 2]}},
            },
            "run": {
                "kind": "dag",
                "operations": [
                    {
                        "name": "echo",
                        "inputs": [{"name": "count", "type": "int"}],
                        "params": {"count": {"ref": "dag", "value": "inputs.count"}},
                        "run": {
                            "kind": "job",
                            "container": {
                                "image": "busybox:1.36",
                                "args": ["echo {{ count }}"],
                                "resources": {"limits": {"nvidia.com/gpu": 1}},
                            },
                        },
                    }
                ],
            },
        }
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        raw_content = run.raw_content

        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=run.id, start=False)

        run.refresh_from_db()
        assert run.status == V1Statuses.COMPILED, run.status_conditions
        assert run.raw_content == raw_content
        dags = list(run.pipeline_runs.order_by("id"))
        assert len(dags) == 2
        for count, dag in enumerate(dags, 1):
            assert dag.is_dag
            assert dag.inputs == {"count": count}
            dag_source = read_polyaxonfile(dag.raw_content)
            assert dag_source.matrix is None
            assert dag_source.run.operations[0].params["count"].ref == "dag"

            with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                SchedulingManager.runs_prepare(run_id=dag.id, start=False)

            dag.refresh_from_db()
            assert dag.status == V1Statuses.COMPILED, dag.status_conditions
            assert dag.inputs == {"count": count}
            leaf = dag.pipeline_runs.get()
            assert leaf.is_job
            assert leaf.name == "echo"
            assert leaf.controller_id == run.id
            assert leaf.pipeline_id == dag.id
            assert leaf.params["count"] == {"value": count}

            with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                SchedulingManager.runs_prepare(run_id=leaf.id, start=False)

            leaf.refresh_from_db()
            assert leaf.status == V1Statuses.COMPILED, leaf.status_conditions
            assert leaf.inputs == {"count": count}
            compiled = CompiledOperationSpecification.read(leaf.content)
            assert compiled.matrix is None
            assert compiled.run.container.args == [f"echo {count}"]
            assert compiled.run.container.resources["limits"]["nvidia.com/gpu"] == 1

    def test_shared_dag_creates_children_and_edges_through_prepare(self):
        for kind in (None, "component", "operation"):
            with self.subTest(kind=kind):
                job = {
                    "kind": "job",
                    "container": {
                        "image": "busybox:1.36",
                        "command": ["sh", "-c"],
                        "args": ["echo {{ count }}"],
                        "resources": {"limits": {"nvidia.com/gpu": 1}},
                    },
                }
                template = {
                    "kind": "operation",
                    "name": "template",
                    "inputs": [
                        {"name": "count", "type": "int"},
                        {"name": "result", "type": "int"},
                    ],
                    "params": {
                        "count": 3,
                        "result": {"ref": "ops.producer", "value": "outputs.result"},
                        "producer_uuid": {
                            "ref": "ops.producer",
                            "value": "globals.uuid",
                            "contextOnly": True,
                        },
                    },
                    "dependencies": ["not-a-node"],
                    "trigger": "all_failed",
                    "conditions": "{{ False }}",
                    "skipOnUpstreamSkip": True,
                    "schedule": {"kind": "cron", "cron": "0 * * * *"},
                    "run": deepcopy(job),
                }
                template["run"]["container"]["args"] = [
                    "echo {{ count }} {{ result }} {{ joined_results[0] }}"
                ]
                source = {
                    "cache": {"disable": True},
                    "run": {
                        "kind": "dag",
                        "components": [
                            template,
                            {"name": "unused", "run": job},
                        ],
                        "operations": [
                            {
                                "kind": "component",
                                "name": "producer",
                                "params": {"count": 3},
                                "outputs": [
                                    {"name": "result", "type": "int", "value": 7}
                                ],
                                "run": job,
                            },
                            {
                                "name": "consumer",
                                "dagRef": "template",
                                "params": {"count": 5},
                                "dependencies": ["producer"],
                                "trigger": "all_succeeded",
                                "conditions": "{{ result == 19 }}",
                                "skipOnUpstreamSkip": False,
                                "joins": [
                                    {
                                        "query": "uuid:{{ producer_uuid }}",
                                        "params": {
                                            "joined_results": {
                                                "value": "outputs.result",
                                                "contextOnly": True,
                                            }
                                        },
                                    }
                                ],
                                "events": [
                                    {
                                        "ref": "ops.producer",
                                        "kinds": ["run_status_succeeded"],
                                    }
                                ],
                            },
                            {
                                "name": "embedded",
                                "component": {"params": {"count": 4}, "run": job},
                            },
                        ],
                    },
                }
                if kind:
                    source["kind"] = kind
                    source["run"]["operations"][1]["kind"] = kind
                response = self.client.post(self.url, {"content": orjson_dumps(source)})
                assert response.status_code == status.HTTP_201_CREATED, response.data
                run = Run.objects.get(uuid=response.data["uuid"])
                raw_content = run.raw_content
                assert read_polyaxonfile(raw_content).kind == kind

                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=run.id, start=False)

                run.refresh_from_db()
                assert run.status == V1Statuses.COMPILED, run.status_conditions
                assert run.raw_content == raw_content
                children = {child.name: child for child in run.pipeline_runs.all()}
                assert set(children) == {"producer", "consumer", "embedded"}
                for name, child in children.items():
                    child_source = read_polyaxonfile(child.raw_content)
                    compiled = CompiledOperationSpecification.read(child.content)
                    assert child_source.name == name
                    assert compiled.name == name
                    assert compiled.run.container.image == "busybox:1.36"
                    assert (
                        compiled.run.container.resources["limits"]["nvidia.com/gpu"]
                        == 1
                    )
                    assert child.pipeline_id == run.id
                    assert child.controller_id == run.id
                    assert child.is_job
                    assert compiled.schedule is None
                    assert compiled.cache.disable is True
                producer_source = read_polyaxonfile(children["producer"].raw_content)
                assert producer_source.kind == "component"
                assert read_polyaxonfile(children["embedded"].raw_content).kind is None
                assert children["embedded"].params["count"] == {"value": 4}

                consumer = children["consumer"]
                consumer_source = read_polyaxonfile(consumer.raw_content)
                consumer_raw_content = consumer.raw_content
                assert consumer_source.kind == kind
                consumer_compiled = CompiledOperationSpecification.read(
                    consumer.content
                )
                assert consumer_source.dag_ref == "template"
                assert consumer_source.component.schedule is not None
                assert consumer_source.component.dependencies == ["not-a-node"]
                assert consumer.params["count"] == {"value": 5}
                assert consumer.params["result"] == {
                    "ref": "ops.producer",
                    "value": "outputs.result",
                }
                assert consumer_compiled.dependencies == ["producer"]
                assert consumer_compiled.trigger == "all_succeeded"
                assert consumer_compiled.conditions == "{{ result == 19 }}"
                assert consumer_compiled.skip_on_upstream_skip is False
                assert consumer_compiled.joins[0].query == "uuid:{{ producer_uuid }}"
                edge = RunEdge.objects.get(downstream=consumer)
                assert edge.upstream_id == children["producer"].id
                assert edge.kind == "dag"
                assert edge.values == {
                    "result": "outputs.result",
                    "producer_uuid": "globals.uuid",
                }
                assert edge.statuses == [V1Statuses.SUCCEEDED]
                assert RunEdge.objects.filter(downstream__pipeline=run).count() == 1

                producer = children["producer"]
                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=producer.id, start=False)

                producer.refresh_from_db()
                assert producer.status == V1Statuses.COMPILED, (
                    producer.status_conditions
                )
                assert producer.original_id is None
                assert producer.inputs == {"count": 3}
                assert producer.outputs == {"result": 7}
                assert producer.gpu == 1
                assert CompiledOperationSpecification.read(
                    producer.content
                ).run.container.args == ["echo 3"]

                producer.outputs = {"result": 19}
                producer.status = V1Statuses.SUCCEEDED
                producer.save(update_fields=["outputs", "status"])
                with patch("haupt.common.workers.send") as workers_send:
                    SchedulingManager.runs_notify_done(run_id=producer.id)
                assert (
                    SchedulerCeleryTasks.RUNS_PREPARE,
                    {"run_id": consumer.id},
                ) in [
                    (call.args[0], call.kwargs.get("kwargs"))
                    for call in workers_send.call_args_list
                ]

                consumer.refresh_from_db()
                assert consumer.status == V1Statuses.CREATED
                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=consumer.id, start=False)

                consumer.refresh_from_db()
                assert consumer.status == V1Statuses.COMPILED, (
                    consumer.status_conditions
                )
                assert consumer.raw_content == consumer_raw_content
                assert consumer.inputs == {
                    "count": 5,
                    "result": 19,
                    "producer_uuid": producer.uuid.hex,
                    "joined_results": [19],
                }
                consumer_compiled = CompiledOperationSpecification.read(
                    consumer.content
                )
                assert consumer_compiled.run.container.args == ["echo 5 19 19"]
                assert consumer_compiled.run.container.image == "busybox:1.36"
                assert consumer.gpu == 1
                assert RunEdge.objects.get(
                    upstream=producer, downstream=consumer, kind="join"
                ).values == {"joined_results": "outputs.result"}

    def test_shared_dag_downstream_trigger_conditions_and_skip_policy(self):
        for upstream_status in (
            V1Statuses.SUCCEEDED,
            V1Statuses.FAILED,
            V1Statuses.SKIPPED,
        ):
            with self.subTest(upstream_status=upstream_status):
                job = {
                    "kind": "job",
                    "container": {"image": "busybox:1.36", "args": ["echo ready"]},
                }
                nodes = [
                    {"name": "success-only", "kind": "component"},
                    {"name": "always", "trigger": "all_done"},
                    {
                        "name": "skip-with-upstream",
                        "kind": "operation",
                        "trigger": "all_done",
                        "skipOnUpstreamSkip": True,
                    },
                    {
                        "name": "false-condition",
                        "kind": "component",
                        "trigger": "all_done",
                        "conditions": "{{ False }}",
                    },
                ]
                source = {
                    "cache": {"disable": True},
                    "run": {
                        "kind": "dag",
                        "operations": [{"name": "producer", "run": job}]
                        + [
                            {"dependencies": ["producer"], "run": job, **node}
                            for node in nodes
                        ],
                    },
                }
                response = self.client.post(self.url, {"content": orjson_dumps(source)})
                assert response.status_code == status.HTTP_201_CREATED, response.data
                run = Run.objects.get(uuid=response.data["uuid"])
                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=run.id, start=False)

                run.refresh_from_db()
                assert run.status == V1Statuses.COMPILED, run.status_conditions
                children = {child.name: child for child in run.pipeline_runs.all()}
                producer = children.pop("producer")
                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=producer.id, start=False)
                producer.refresh_from_db()
                assert producer.status == V1Statuses.COMPILED, (
                    producer.status_conditions
                )
                producer.status = upstream_status
                producer.save(update_fields=["status"])

                with patch("haupt.common.workers.send") as workers_send:
                    SchedulingManager.runs_notify_done(run_id=producer.id)

                queued = {"always", "false-condition"}
                if upstream_status == V1Statuses.SUCCEEDED:
                    queued.add("success-only")
                if upstream_status != V1Statuses.SKIPPED:
                    queued.add("skip-with-upstream")
                assert {
                    call.kwargs["kwargs"]["run_id"]
                    for call in workers_send.call_args_list
                    if call.args[0] == SchedulerCeleryTasks.RUNS_PREPARE
                } == {children[name].id for name in queued}

                for name, child in children.items():
                    child.refresh_from_db()
                    if name not in queued:
                        expected = (
                            V1Statuses.SKIPPED
                            if name == "skip-with-upstream"
                            else V1Statuses.UPSTREAM_FAILED
                        )
                        assert child.status == expected, child.status_conditions
                        continue
                    assert child.status == V1Statuses.CREATED
                    with patch.object(
                        polyaxon_settings, "AGENT_CONFIG", self.agent_config
                    ):
                        SchedulingManager.runs_prepare(run_id=child.id, start=False)
                    child.refresh_from_db()
                    expected = (
                        V1Statuses.SKIPPED
                        if name == "false-condition"
                        else V1Statuses.COMPILED
                    )
                    assert child.status == expected, child.status_conditions
                    if expected == V1Statuses.COMPILED:
                        assert CompiledOperationSpecification.read(
                            child.content
                        ).run.container.args == ["echo ready"]

    def test_shared_dag_binds_template_params_and_keeps_patch_precedence(self):
        for count in (0, 3):
            with self.subTest(count=count):
                job = {
                    "kind": "job",
                    "container": {
                        "image": "busybox:1.36",
                        "command": ["sh", "-c"],
                        "args": ["echo {{ count }}"],
                    },
                }
                template = {
                    "kind": "operation",
                    "name": "template",
                    "component": {
                        "kind": "component",
                        "cache": {"disable": True},
                        "strictParams": True,
                        "inputs": [{"name": "count", "type": "int"}],
                        "params": {
                            "count": {"ref": "dag", "value": "inputs.count"},
                            "parent_uuid": {
                                "ref": "dag",
                                "value": "globals.uuid",
                                "contextOnly": True,
                            },
                        },
                        "run": job,
                    },
                }
                source = {
                    "cache": {"disable": True},
                    "inputs": [{"name": "count", "type": "int"}],
                    "params": {"count": count},
                    "run": {
                        "kind": "dag",
                        "components": [template],
                        "operations": [
                            {"name": "inherited", "dagRef": "template"},
                            {
                                "name": "patched",
                                "dagRef": "template",
                                "params": {"count": 5},
                                "run": {"container": {"image": "busybox:1.37"}},
                            },
                            {
                                "kind": "component",
                                "name": "direct",
                                "params": {
                                    "count": {"ref": "dag", "value": "inputs.count"}
                                },
                                "run": job,
                            },
                        ]
                        + [
                            {
                                "name": strategy,
                                "dagRef": "template",
                                "patchStrategy": strategy,
                                "params": {"count": 5},
                            }
                            for strategy in (
                                "post_merge",
                                "pre_merge",
                                "replace",
                                "isnull",
                            )
                        ],
                    },
                }
                response = self.client.post(self.url, {"content": orjson_dumps(source)})
                assert response.status_code == status.HTTP_201_CREATED, response.data
                run = Run.objects.get(uuid=response.data["uuid"])
                raw_content = run.raw_content

                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=run.id, start=False)

                run.refresh_from_db()
                assert run.status == V1Statuses.COMPILED, run.status_conditions
                assert run.raw_content == raw_content
                children = {child.name: child for child in run.pipeline_runs.all()}
                expected_counts = {
                    "inherited": count,
                    "patched": 5,
                    "direct": count,
                    "post_merge": 5,
                    "pre_merge": count,
                    "replace": 5,
                    "isnull": count,
                }
                assert set(children) == set(expected_counts)
                for name, expected in expected_counts.items():
                    child = children[name]
                    child_raw_content = child.raw_content
                    child_source = read_polyaxonfile(child_raw_content)
                    if name == "patched":
                        assert child_source.run == {
                            "container": {"image": "busybox:1.37"}
                        }
                    if name == "direct":
                        assert child_source.params["count"].value == count
                        assert child_source.params["count"].ref is None
                    else:
                        bound = child_source.component.component.params
                        assert bound["count"].value == count
                        assert bound["count"].ref is None
                        assert bound["parent_uuid"].value == run.uuid.hex
                        assert bound["parent_uuid"].context_only is True
                    expected_inputs = {"count": expected}
                    if name not in ("direct", "replace"):
                        expected_inputs["parent_uuid"] = run.uuid.hex
                    assert child.inputs == expected_inputs
                    assert child.params["count"] == {"value": expected}

                    with patch.object(
                        polyaxon_settings, "AGENT_CONFIG", self.agent_config
                    ):
                        SchedulingManager.runs_prepare(run_id=child.id, start=False)

                    child.refresh_from_db()
                    assert child.status == V1Statuses.COMPILED, child.status_conditions
                    assert child.raw_content == child_raw_content
                    assert child.inputs == expected_inputs
                    compiled = CompiledOperationSpecification.read(child.content)
                    assert compiled.run.kind == V1RunKind.JOB
                    assert compiled.run.container.image == (
                        "busybox:1.37" if name == "patched" else "busybox:1.36"
                    )
                    assert compiled.run.container.command == ["sh", "-c"]
                    assert compiled.run.container.args == [f"echo {expected}"]

                inherited = children["inherited"]
                assert read_polyaxonfile(inherited.raw_content).params is None
                with patch("haupt.common.workers.send"):
                    response = self.client.post(
                        f"{self.url}{inherited.uuid.hex}/restart/", {}
                    )
                assert response.status_code == status.HTTP_201_CREATED, response.data
                restarted = Run.objects.get(uuid=response.data["uuid"])
                assert restarted.original_id == inherited.id
                assert restarted.pipeline_id is None
                assert restarted.params == inherited.params
                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=restarted.id, start=False)
                restarted.refresh_from_db()
                assert restarted.status == V1Statuses.COMPILED, (
                    restarted.status_conditions
                )
                assert restarted.inputs == inherited.inputs
                assert CompiledOperationSpecification.read(
                    restarted.content
                ).run.container.args == [f"echo {count}"]

    def test_shared_dag_creates_nested_dag_and_inherits_node_matrix(self):
        source = {
            "kind": "component",
            "cache": {"disable": True},
            "inputs": [{"name": "count", "type": "int"}],
            "params": {"count": 3},
            "run": {
                "kind": "dag",
                "components": [
                    {
                        "kind": "operation",
                        "name": "search-template",
                        "inputs": [{"name": "seed", "type": "int"}],
                        "params": {"message": "hello"},
                        "matrix": {
                            "kind": "grid",
                            "params": {"seed": {"kind": "choice", "value": [1, 2]}},
                        },
                        "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
                    }
                ],
                "operations": [
                    {"name": "search", "dagRef": "search-template"},
                    {
                        "name": "nested",
                        "inputs": [{"name": "count", "type": "int"}],
                        "params": {"count": 9},
                        "run": {
                            "kind": "dag",
                            "operations": [
                                {
                                    "kind": "component",
                                    "name": "leaf",
                                    "params": {
                                        "count": {"ref": "dag", "value": "inputs.count"}
                                    },
                                    "run": {
                                        "kind": "job",
                                        "container": {
                                            "image": "busybox:1.36",
                                            "args": ["echo {{ count }}"],
                                        },
                                    },
                                }
                            ],
                        },
                    },
                ],
            },
        }
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])

        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=run.id, start=False)

        run.refresh_from_db()
        assert run.status == V1Statuses.COMPILED, run.status_conditions
        children = {child.name: child for child in run.pipeline_runs.all()}
        assert set(children) == {"search", "nested"}
        search = children["search"]
        assert search.is_matrix
        assert search.params == {"message": {"value": "hello"}}
        search_compiled = CompiledOperationSpecification.read(search.content)
        assert search_compiled.matrix.kind == "grid"

        search_raw_content = search.raw_content
        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=search.id, start=False)
        search.refresh_from_db()
        assert search.status == V1Statuses.COMPILED, search.status_conditions
        assert search.raw_content == search_raw_content
        matrix_children = list(search.pipeline_runs.order_by("id"))
        assert len(matrix_children) == 2
        for seed, child in enumerate(matrix_children, 1):
            assert child.is_job
            assert child.pipeline_id == search.id
            assert child.controller_id == run.id
            assert child.inputs == {"seed": seed, "message": "hello"}
            child_source = read_polyaxonfile(child.raw_content)
            assert child_source.dag_ref == "search-template"
            assert child_source.component.matrix is None

            with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                SchedulingManager.runs_prepare(run_id=child.id, start=False)

            child.refresh_from_db()
            assert child.status == V1Statuses.COMPILED, child.status_conditions
            assert child.inputs == {"seed": seed, "message": "hello"}
            compiled = CompiledOperationSpecification.read(child.content)
            assert compiled.matrix is None
            assert compiled.inputs[0].value == seed
            assert compiled.contexts[0].value == "hello"

        nested = children["nested"]
        assert nested.is_dag
        nested_source = read_polyaxonfile(nested.raw_content)
        assert nested_source.run.operations[0].params["count"].ref == "dag"

        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=nested.id, start=False)

        nested.refresh_from_db()
        assert nested.status == V1Statuses.COMPILED, nested.status_conditions
        leaf = nested.pipeline_runs.get()
        assert leaf.name == "leaf"
        assert leaf.controller_id == run.id
        assert leaf.pipeline_id == nested.id
        assert read_polyaxonfile(leaf.raw_content).kind == "component"
        assert leaf.params == {"count": {"value": 9}}
        leaf_compiled = CompiledOperationSpecification.read(leaf.content)
        assert leaf_compiled.run.container.image == "busybox:1.36"

        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=leaf.id, start=False)
        leaf.refresh_from_db()
        assert leaf.status == V1Statuses.COMPILED, leaf.status_conditions
        assert leaf.inputs == {"count": 9}
        assert CompiledOperationSpecification.read(leaf.content).run.container.args == [
            "echo 9"
        ]

    def test_shared_dag_explicit_nulls_survive_prepare_and_child_restart(self):
        for field, nested in (
            ("operations", False),
            ("components", False),
            ("operations", True),
            ("components", True),
        ):
            with self.subTest(field=field, nested=nested):
                template = {
                    "name": "train",
                    "strictParams": True,
                    "inputs": [{"name": "count", "type": "int"}],
                    "params": {"count": {"ref": "dag", "value": "inputs.count"}},
                    "schedule": {"kind": "cron", "cron": "0 * * * *"},
                    "matrix": {
                        "kind": "grid",
                        "params": {"count": {"kind": "choice", "value": [1, 2]}},
                    },
                    "run": {
                        "kind": "job",
                        "container": {
                            "image": "busybox:1.36",
                            "args": ["echo {{ count }}"],
                        },
                    },
                }
                node = {"name": "once", "dagRef": "train"}
                if field == "operations":
                    node.update({"matrix": None, "schedule": None})
                else:
                    template = {
                        "name": "train",
                        "component": template,
                        "matrix": None,
                        "schedule": None,
                    }
                source = {
                    "cache": {"disable": True},
                    "inputs": [{"name": "count", "type": "int"}],
                    "params": {"count": 3},
                    "run": {
                        "kind": "dag",
                        "components": [template],
                        "operations": [node],
                    },
                }
                if nested:
                    source = {
                        "cache": {"disable": True},
                        "run": {
                            "kind": "dag",
                            "components": [{"name": "nested-template", **source}],
                            "operations": [
                                {"name": "nested", "dagRef": "nested-template"}
                            ],
                        },
                    }
                response = self.client.post(self.url, {"content": orjson_dumps(source)})
                assert response.status_code == status.HTTP_201_CREATED, response.data
                root = Run.objects.get(uuid=response.data["uuid"])
                saved_dag = orjson_loads(root.content)["run"]
                if nested:
                    saved_dag = saved_dag["components"][0]["run"]
                parent = root
                child_kinds = (
                    (V1RunKind.DAG, V1RunKind.JOB) if nested else (V1RunKind.JOB,)
                )
                for child_kind in child_kinds:
                    raw_content = parent.raw_content

                    with (
                        patch.object(
                            polyaxon_settings, "AGENT_CONFIG", self.agent_config
                        ),
                        patch.object(
                            V1Polyaxonfile,
                            "to_source_json",
                            autospec=True,
                            side_effect=V1Polyaxonfile.to_source_json,
                        ) as serialize_source,
                    ):
                        SchedulingManager.runs_prepare(run_id=parent.id, start=False)

                    serialize_source.assert_called_once()
                    parent.refresh_from_db()
                    assert parent.status == V1Statuses.COMPILED, (
                        parent.status_conditions
                    )
                    assert parent.raw_content == raw_content
                    child = parent.pipeline_runs.get()
                    assert child.kind == child_kind
                    assert child.pipeline_id == parent.id
                    assert child.controller_id == root.id
                    if child_kind == V1RunKind.DAG:
                        parent = child

                child_raw_content = child.raw_content
                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=child.id, start=False)
                child.refresh_from_db()
                assert child.status == V1Statuses.COMPILED, child.status_conditions
                assert child.inputs == {"count": 3}
                assert not child.pipeline_runs.exists()
                child_compiled = CompiledOperationSpecification.read(child.content)
                assert child_compiled.matrix is None
                assert child_compiled.schedule is None
                assert child_compiled.run.container.args == ["echo 3"]

                with patch("haupt.common.workers.send"):
                    response = self.client.post(
                        f"{self.url}{child.uuid.hex}/restart/", {}
                    )
                assert response.status_code == status.HTTP_201_CREATED, response.data
                restarted = Run.objects.get(uuid=response.data["uuid"])
                assert restarted.original_id == child.id
                assert restarted.pipeline_id is None
                assert restarted.kind == V1RunKind.JOB

                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=restarted.id, start=False)

                restarted.refresh_from_db()
                assert restarted.status == V1Statuses.COMPILED, (
                    restarted.status_conditions
                )
                assert restarted.inputs == {"count": 3}
                assert not restarted.pipeline_runs.exists()
                compiled = CompiledOperationSpecification.read(restarted.content)
                assert compiled.matrix is None
                assert compiled.schedule is None
                assert compiled.run.container.args == ["echo 3"]
                assert child.raw_content == child_raw_content
                assert restarted.raw_content == child_raw_content
                assert saved_dag[field][0]["matrix"] is None
                assert saved_dag[field][0]["schedule"] is None
                child_source = read_polyaxonfile(restarted.raw_content)
                assert child_source.dag_ref == "train"
                cleared = (
                    child_source if field == "operations" else child_source.component
                )
                assert {"matrix", "schedule"} <= cleared.model_fields_set
                assert cleared.matrix is None
                assert cleared.schedule is None
                bound = child_source.component
                if field == "components":
                    bound = bound.component
                assert bound.params["count"].value == 3
                assert bound.params["count"].ref is None

    def test_shared_dag_rejects_node_schedule_without_creating_children(self):
        source = {
            "run": {
                "kind": "dag",
                "operations": [
                    {
                        "name": "train",
                        "schedule": {"kind": "cron", "cron": "0 * * * *"},
                        "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
                    }
                ],
            }
        }
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])

        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=run.id, start=False)

        run.refresh_from_db()
        assert run.status == V1Statuses.FAILED
        assert "train" in run.status_conditions[-1]["message"]
        assert "cannot define a schedule" in run.status_conditions[-1]["message"]
        assert not run.pipeline_runs.exists()

    def test_shared_dag_rejects_kindless_patch_for_template_runtime(self):
        source = {
            "run": {
                "kind": "dag",
                "components": [
                    {
                        "name": "template",
                        "run": {
                            "kind": "job",
                            "container": {"image": "busybox:1.36"},
                        },
                    }
                ],
                "operations": [
                    {"name": "train", "dagRef": "template", "run": {"ports": [8080]}}
                ],
            }
        }
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        raw_content = run.raw_content
        assert read_polyaxonfile(raw_content).run.operations[0].run == {"ports": [8080]}

        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=run.id, start=False)

        run.refresh_from_db()
        assert run.status == V1Statuses.FAILED, run.status_conditions
        assert "ports" in run.status_conditions[-1]["message"]
        assert run.raw_content == raw_content
        assert not run.pipeline_runs.exists()

    def test_shared_jobs_and_services_through_prepare(self):
        for runtime in (V1RunKind.JOB, V1RunKind.SERVICE):
            for kind in (None, "component", "operation", "legacy", "patched"):
                with self.subTest(runtime=runtime, kind=kind):
                    source = {
                        "version": 1.1,
                        "inputs": [{"name": "count", "type": "int"}],
                        "outputs": [{"name": "result", "type": "int", "value": 7}],
                        "params": {
                            "count": 3,
                            "message": {"value": "hello", "contextOnly": True},
                            "label": "shared",
                        },
                        "run": {
                            "kind": runtime,
                            "container": {
                                "image": "busybox:1.36",
                                "command": ["sh", "-c"],
                                "args": ["echo {{ count }} {{ message }} {{ label }}"],
                                "resources": {"limits": {"nvidia.com/gpu": 1}},
                            },
                        },
                    }
                    if runtime == V1RunKind.SERVICE:
                        source["run"]["ports"] = [8080]
                    if kind == "patched":
                        source = {
                            "component": source,
                            "run": {"container": {"image": "busybox:1.37"}},
                        }
                    elif kind == "legacy":
                        params = source.pop("params")
                        source = {
                            "kind": "operation",
                            "params": params,
                            "component": source,
                        }
                    elif kind:
                        source["kind"] = kind
                    expected_source = read_polyaxonfile(source).to_dict()

                    with patch.object(
                        V1Polyaxonfile,
                        "to_source_json",
                        autospec=True,
                        side_effect=V1Polyaxonfile.to_source_json,
                    ) as serialize_source:
                        response = self.client.post(
                            self.url, {"content": orjson_dumps(source)}
                        )

                    assert response.status_code == status.HTTP_201_CREATED, (
                        response.data
                    )
                    serialize_source.assert_called_once()
                    run = Run.objects.get(uuid=response.data["uuid"])
                    raw_content = run.raw_content
                    assert read_polyaxonfile(raw_content).to_dict() == expected_source
                    assert run.kind == runtime
                    assert run.runtime == runtime
                    assert run.inputs == {
                        "count": 3,
                        "message": "hello",
                        "label": "shared",
                    }
                    assert run.params == {
                        "count": {"value": 3},
                        "message": {"value": "hello", "contextOnly": True},
                        "label": {"value": "shared"},
                    }
                    compiled = CompiledOperationSpecification.read(run.content)
                    assert compiled.kind == "compiled_operation"
                    assert compiled.run.kind == runtime
                    assert compiled.run.container.image == (
                        "busybox:1.37" if kind == "patched" else "busybox:1.36"
                    )
                    assert compiled.run.container.command == ["sh", "-c"]
                    assert compiled.inputs[0].name == "count"
                    assert compiled.outputs[0].name == "result"
                    assert [io.name for io in compiled.contexts] == ["message"]
                    assert not (
                        {"params", "component", "runPatch"} & compiled.to_dict().keys()
                    )

                    with patch.object(
                        polyaxon_settings, "AGENT_CONFIG", self.agent_config
                    ):
                        SchedulingManager.runs_prepare(run_id=run.id, start=False)

                    run.refresh_from_db()
                    assert run.status == V1Statuses.COMPILED, run.status_conditions
                    assert run.raw_content == raw_content
                    assert run.inputs == {
                        "count": 3,
                        "message": "hello",
                        "label": "shared",
                    }
                    assert run.outputs == {"result": 7}
                    assert run.gpu == 1
                    compiled = CompiledOperationSpecification.read(run.content)
                    assert compiled.run.kind == runtime
                    assert compiled.run.container.image == (
                        "busybox:1.37" if kind == "patched" else "busybox:1.36"
                    )
                    assert compiled.run.container.command == ["sh", "-c"]
                    assert compiled.run.container.args == ["echo 3 hello shared"]
                    if runtime == V1RunKind.SERVICE:
                        assert compiled.run.ports == [8080]

    def test_embedded_params_and_runtime_follow_patch_strategy(self):
        for strategy, image, count in (
            (None, "local:v2", 5),
            ("post_merge", "final:v3", 5),
            ("pre_merge", "busybox:1.36", 3),
            ("replace", "local:v2", 5),
            ("isnull", "busybox:1.36", 3),
        ):
            with self.subTest(strategy=strategy):
                source = {
                    "kind": "component",
                    "component": {
                        "kind": "operation",
                        "params": {"count": 3, "message": "inherited"},
                        "run": {
                            "kind": "job",
                            "container": {
                                "image": "busybox:1.36",
                                "args": ["echo {{ count }}"],
                            },
                        },
                    },
                    "params": {"count": 5},
                    "run": {
                        "container": {"image": "local:v2", "args": ["echo {{ count }}"]}
                    },
                }
                if strategy:
                    source["patchStrategy"] = strategy
                if strategy == "post_merge":
                    source["runPatch"] = {"container": {"image": "final:v3"}}
                response = self.client.post(self.url, {"content": orjson_dumps(source)})
                assert response.status_code == status.HTTP_201_CREATED, response.data
                run = Run.objects.get(uuid=response.data["uuid"])
                assert run.params["count"] == {"value": count}
                if strategy != "replace":
                    assert run.params["message"] == {"value": "inherited"}
                assert read_polyaxonfile(run.raw_content).component.kind == "operation"
                compiled = CompiledOperationSpecification.read(run.content)
                assert compiled.run.container.image == image

                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=run.id, start=False)

                run.refresh_from_db()
                assert run.status == V1Statuses.COMPILED, run.status_conditions
                assert run.inputs["count"] == count
                compiled = CompiledOperationSpecification.read(run.content)
                assert compiled.run.container.image == image

    def test_strict_params_are_checked_during_prepare(self):
        for context_only in (None, False, True):
            with self.subTest(context_only=context_only):
                source = {
                    "strictParams": False,
                    "component": {
                        "kind": "operation",
                        "strictParams": True,
                        "params": {"message": {"value": "hello"}},
                        "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
                    },
                }
                if context_only is not None:
                    source["component"]["params"]["message"]["contextOnly"] = (
                        context_only
                    )
                response = self.client.post(self.url, {"content": orjson_dumps(source)})
                assert response.status_code == status.HTTP_201_CREATED, response.data
                run = Run.objects.get(uuid=response.data["uuid"])
                compiled = CompiledOperationSpecification.read(run.content)
                assert compiled.strict_params is True

                with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                    SchedulingManager.runs_prepare(run_id=run.id, start=False)

                run.refresh_from_db()
                if context_only:
                    assert run.status == V1Statuses.COMPILED, run.status_conditions
                    assert run.inputs == {"message": "hello"}
                else:
                    assert run.status == V1Statuses.FAILED
                    expected_error = (
                        "Param `message` requires a matching input/output declaration."
                        if context_only is False
                        else "Received undeclared param `message`"
                    )
                    assert expected_error in run.status_conditions[-1]["message"]

    def test_invalid_run_sources_do_not_create_runs(self):
        for source in (
            {"kind": "component", "params": {"count": 3}},
            {"kind": "operation", "component": {"params": {"count": 3}}},
            {"run": {"kind": "unknown"}},
            {
                "component": {
                    "run": {"kind": "job", "container": {"image": "busybox:1.36"}}
                },
                "run": {"ports": [8080]},
            },
            {"runPatch": {"container": {"image": "busybox:1.36"}}},
            {"pathRef": "/client-only/base.yaml"},
            {"hubRef": {"name": "invalid"}},
            {"component": "run: {kind: job, container: {image: busybox:1.36}}"},
            {
                "template": {"enabled": True},
                "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
            },
            {"kind": "compiled_operation", "run": {"kind": "job"}},
        ):
            with self.subTest(source=source):
                response = self.client.post(self.url, {"content": orjson_dumps(source)})
                assert response.status_code == status.HTTP_400_BAD_REQUEST, (
                    response.data
                )
                assert not Run.objects.filter(project=self.project).exists()

    def test_malformed_yaml_does_not_create_run(self):
        for content in ("run: !unknown {}", "kind: component\n---\nkind: operation"):
            with self.subTest(content=content):
                response = self.client.post(self.url, {"content": content})
                assert response.status_code == status.HTTP_400_BAD_REQUEST, (
                    response.data
                )
                assert not Run.objects.exists()

    def test_register_shared_file_then_submit_saved_content(self):
        for runtime in (V1RunKind.JOB, V1RunKind.SERVICE):
            for kind in (None, "component", "operation"):
                with self.subTest(runtime=runtime, kind=kind):
                    source = {
                        "params": {"image": "busybox:1.36", "message": "registered"},
                        "run": {
                            "kind": runtime,
                            "container": {
                                "image": "{{ image }}",
                                "args": ["echo {{ message }}"],
                            },
                        },
                    }
                    if kind:
                        source["kind"] = kind
                    content = orjson_dumps(source)
                    run_count = Run.objects.count()
                    response = self.client.post(
                        self.version_url,
                        {"name": f"{runtime}-{kind or 'kindless'}", "content": content},
                    )
                    assert response.status_code == status.HTTP_201_CREATED, (
                        response.data
                    )
                    version = ProjectVersion.objects.get(uuid=response.data["uuid"])
                    assert Run.objects.count() == run_count
                    assert version.run_id is None
                    assert version.user_id is None
                    assert version.content == content
                    spec = read_polyaxonfile(version.content)
                    assert version.state == get_component_version_state(spec)
                    assert spec.kind == kind

                    response = self.client.post(
                        self.url,
                        {
                            "content": orjson_dumps(
                                {
                                    "component": spec.to_dict(),
                                    "params": {"message": "local"},
                                }
                            )
                        },
                    )
                    assert response.status_code == status.HTTP_201_CREATED, (
                        response.data
                    )
                    run = Run.objects.get(uuid=response.data["uuid"])
                    assert run.kind == runtime
                    assert run.inputs == {"image": "busybox:1.36", "message": "local"}
                    with patch.object(
                        polyaxon_settings, "AGENT_CONFIG", self.agent_config
                    ):
                        SchedulingManager.runs_prepare(run_id=run.id, start=False)
                    run.refresh_from_db()
                    assert run.status == V1Statuses.COMPILED, run.status_conditions
                    compiled = CompiledOperationSpecification.read(run.content)
                    assert compiled.run.container.image == "busybox:1.36"
                    assert compiled.run.container.args == ["echo local"]

    def test_register_explicit_nulls_then_submit_saved_content(self):
        source = {
            "component": {
                "schedule": {"kind": "cron", "cron": "0 * * * *"},
                "matrix": {
                    "kind": "grid",
                    "params": {"count": {"kind": "choice", "value": [1, 2]}},
                },
                "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
            },
            "schedule": None,
            "matrix": None,
        }
        content = orjson_dumps(source)
        response = self.client.post(
            self.version_url, {"name": "explicit-nulls", "content": content}
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        version = ProjectVersion.objects.get(uuid=response.data["uuid"])

        response = self.client.post(self.url, {"content": version.content})

        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        assert run.kind == V1RunKind.JOB
        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=run.id, start=False)
        run.refresh_from_db()
        assert run.status == V1Statuses.COMPILED, run.status_conditions
        assert not run.pipeline_runs.exists()
        compiled = CompiledOperationSpecification.read(run.content)
        assert compiled.schedule is None
        assert compiled.matrix is None
        assert compiled.run.kind == V1RunKind.JOB
        assert version.content == content
        assert orjson_loads(run.raw_content) == source

    def test_root_container_through_register_submit_and_reruns(self):
        def prepare(run):
            with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
                SchedulingManager.runs_prepare(run_id=run.id, start=False)
            run.refresh_from_db()
            assert run.status == V1Statuses.COMPILED, run.status_conditions
            return CompiledOperationSpecification.read(run.content).run

        def assert_container(runtime, expected):
            assert runtime.kind == V1RunKind.JOB
            for key, value in expected.items():
                assert getattr(runtime.container, key) == value

        native = {
            "image": "native:v1",
            "command": ["sh", "-c"],
            "args": ["echo native"],
        }
        root = {"image": "busybox:1.36", "command": ["echo"], "args": ["hello"]}
        cases = (
            ("standalone", {"container": root}, root),
            (
                "with-run",
                {
                    "kind": "component",
                    "run": {"kind": "job", "container": native},
                    "container": {"image": "busybox:1.36"},
                },
                {**native, "image": "busybox:1.36"},
            ),
        )
        for name, source, expected in cases:
            with self.subTest(name=name):
                content = orjson_dumps(source)
                run_count = Run.objects.count()
                response = self.client.post(
                    self.version_url, {"name": name, "content": content}
                )
                assert response.status_code == status.HTTP_201_CREATED, response.data
                version = ProjectVersion.objects.get(uuid=response.data["uuid"])
                assert Run.objects.count() == run_count
                assert version.content == content
                assert version.state == get_component_version_state(
                    read_polyaxonfile(content)
                )

                response = self.client.post(self.url, {"content": version.content})
                assert response.status_code == status.HTTP_201_CREATED, response.data
                run = Run.objects.get(uuid=response.data["uuid"])
                assert run.kind == V1RunKind.JOB
                assert orjson_loads(run.raw_content) == source
                assert_container(prepare(run), expected)

                # An outer root container overrides the registered one.
                wrapped = {
                    "kind": "operation",
                    "component": source,
                    "container": {"image": "local:v1"},
                }
                response = self.client.post(
                    self.url, {"content": orjson_dumps(wrapped)}
                )
                assert response.status_code == status.HTTP_201_CREATED, response.data
                local = Run.objects.get(uuid=response.data["uuid"])
                assert orjson_loads(local.raw_content) == wrapped
                assert_container(prepare(local), {**expected, "image": "local:v1"})

                run_url = f"{self.url}{run.uuid.hex}/"
                override = {"container": {"image": "restart:v2"}}
                with patch("haupt.common.workers.send"):
                    response = self.client.post(
                        run_url + "restart/", {"content": orjson_dumps(override)}
                    )
                assert response.status_code == status.HTTP_201_CREATED, response.data
                restarted = Run.objects.get(uuid=response.data["uuid"])
                assert restarted.original_id == run.id
                assert orjson_loads(restarted.raw_content) == source
                assert_container(
                    prepare(restarted), {**expected, "image": "restart:v2"}
                )

                with patch("haupt.common.workers.send"):
                    response = self.client.post(run_url + "copy/", {})
                assert response.status_code == status.HTTP_201_CREATED, response.data
                copied = Run.objects.get(uuid=response.data["uuid"])
                assert orjson_loads(copied.raw_content) == source
                assert_container(prepare(copied), expected)

                new_run_status(
                    run,
                    condition=V1StatusCondition.get_condition(
                        type=V1Statuses.STOPPED, status=True
                    ),
                )
                override = {"container": {"image": "resume:v3"}}
                with patch("haupt.common.workers.send"):
                    response = self.client.post(
                        run_url + "resume/", {"content": orjson_dumps(override)}
                    )
                assert response.status_code == status.HTTP_201_CREATED, response.data
                run.refresh_from_db()
                assert orjson_loads(run.raw_content) == source
                assert_container(
                    CompiledOperationSpecification.read(run.content).run,
                    {**expected, "image": "resume:v3"},
                )

    def test_register_invocation_fields_without_creating_runs(self):
        for kind in (None, "component", "operation"):
            with self.subTest(kind=kind):
                source = {
                    "params": {"count": 3},
                    "matrix": {
                        "kind": "grid",
                        "params": {"seed": {"kind": "choice", "value": [1, 2]}},
                    },
                    "schedule": {"kind": "cron", "cron": "0 * * * *"},
                    "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
                }
                if kind:
                    source["kind"] = kind
                response = self.client.post(
                    self.version_url,
                    {"name": kind or "kindless", "content": orjson_dumps(source)},
                )
                assert response.status_code == status.HTTP_201_CREATED, response.data
                version = ProjectVersion.objects.get(uuid=response.data["uuid"])
                assert version.content == orjson_dumps(source)
                assert version.run_id is None
                assert version.user_id is None
                assert not Run.objects.exists()

    def test_register_partial_file_and_update_preserve_kind_and_state(self):
        source = {"kind": "operation", "params": {"count": 3}}
        response = self.client.post(
            self.version_url, {"name": "partial", "content": orjson_dumps(source)}
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        version = ProjectVersion.objects.get(uuid=response.data["uuid"])
        assert version.user_id is None
        previous_state = version.state
        updated = deepcopy(source)
        updated["params"]["count"] = 5
        response = self.client.patch(
            f"{self.version_url}/partial", {"content": orjson_dumps(updated)}
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        version.refresh_from_db()
        assert version.content == orjson_dumps(updated)
        assert version.state != previous_state
        spec = read_polyaxonfile(version.content)
        assert version.state == get_component_version_state(spec)
        assert spec.kind == "operation"
        assert not Run.objects.exists()

        source = {
            "component": spec.to_dict(),
            "run": {
                "kind": "job",
                "container": {"image": "busybox:1.36", "args": ["echo {{ count }}"]},
            },
        }
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        assert run.inputs == {"count": 5}

        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=run.id, start=False)

        run.refresh_from_db()
        assert run.status == V1Statuses.COMPILED, run.status_conditions
        compiled = CompiledOperationSpecification.read(run.content)
        assert compiled.run.container.args == ["echo 5"]
