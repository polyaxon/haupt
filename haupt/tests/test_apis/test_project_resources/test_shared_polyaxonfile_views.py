from copy import deepcopy
import pytest
from unittest.mock import patch

from rest_framework import status

from clipped.utils.json import orjson_dumps
from haupt.db.factories.projects import ProjectFactory
from haupt.db.managers.versions import get_component_version_state
from haupt.db.models.project_versions import ProjectVersion
from haupt.db.models.runs import Run
from haupt.orchestration.scheduler.manager import SchedulingManager
from polyaxon import settings as polyaxon_settings
from polyaxon._connections import V1BucketConnection, V1Connection, V1ConnectionKind
from polyaxon._polyaxonfile import CompiledOperationSpecification
from polyaxon._polyaxonfile.specs import read_polyaxonfile
from polyaxon._schemas.agent import AgentConfig
from polyaxon.api import API_V1
from polyaxon.schemas import V1RunKind, V1Statuses
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

    def test_shared_jobs_and_services_through_prepare(self):
        for runtime in (V1RunKind.JOB, V1RunKind.SERVICE):
            for kind in (None, "component", "operation", "legacy"):
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
                    if kind == "legacy":
                        params = source.pop("params")
                        source = {
                            "kind": "operation",
                            "params": params,
                            "component": source,
                        }
                    elif kind:
                        source["kind"] = kind
                    expected_source = read_polyaxonfile(source).to_dict()

                    response = self.client.post(
                        self.url, {"content": orjson_dumps(source)}
                    )

                    assert response.status_code == status.HTTP_201_CREATED, (
                        response.data
                    )
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
