import pytest
from unittest.mock import patch

from rest_framework import status

from clipped.utils.json import orjson_dumps, orjson_loads
from haupt.db.factories.projects import ProjectFactory
from haupt.db.managers.statuses import new_run_status
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
from polyaxon.schemas import V1RunKind, V1StatusCondition, V1Statuses
from tests.base.case import BaseTest


@pytest.mark.projects_resources_mark
class TestShortcutPolyaxonfileViews(BaseTest):
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

    def prepare(self, run):
        with patch.object(polyaxon_settings, "AGENT_CONFIG", self.agent_config):
            SchedulingManager.runs_prepare(run_id=run.id, start=False)
        run.refresh_from_db()
        assert run.status == V1Statuses.COMPILED, run.status_conditions
        return CompiledOperationSpecification.read(run.content).run

    @staticmethod
    def assert_container(runtime, expected):
        assert runtime.kind == V1RunKind.JOB
        for key, value in expected.items():
            assert getattr(runtime.container, key) == value

    def test_container_through_register_submit_and_reruns(self):
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
                self.assert_container(self.prepare(run), expected)

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
                self.assert_container(
                    self.prepare(local), {**expected, "image": "local:v1"}
                )

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
                self.assert_container(
                    self.prepare(restarted), {**expected, "image": "restart:v2"}
                )

                with patch("haupt.common.workers.send"):
                    response = self.client.post(run_url + "copy/", {})
                assert response.status_code == status.HTTP_201_CREATED, response.data
                copied = Run.objects.get(uuid=response.data["uuid"])
                assert orjson_loads(copied.raw_content) == source
                self.assert_container(self.prepare(copied), expected)

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
                self.assert_container(
                    CompiledOperationSpecification.read(run.content).run,
                    {**expected, "image": "resume:v3"},
                )

    def test_cmd_through_submit_and_restart(self):
        source = {
            "container": {"image": "busybox:1.36"},
            "cmd": ["export MESSAGE=hello", "echo $MESSAGE"],
        }
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        assert run.kind == V1RunKind.JOB
        assert orjson_loads(run.raw_content) == source
        self.assert_container(
            self.prepare(run),
            {
                "image": "busybox:1.36",
                "command": ["/bin/sh", "-c"],
                "args": ["set -e\nexport MESSAGE=hello\necho $MESSAGE"],
            },
        )

        override = {"cmd": "echo restarted"}
        with patch("haupt.common.workers.send"):
            response = self.client.post(
                f"{self.url}{run.uuid.hex}/restart/",
                {"content": orjson_dumps(override)},
            )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        restarted = Run.objects.get(uuid=response.data["uuid"])
        assert orjson_loads(restarted.raw_content) == source
        self.assert_container(
            self.prepare(restarted),
            {
                "image": "busybox:1.36",
                "command": ["/bin/sh", "-c"],
                "args": ["set -e\necho restarted"],
            },
        )

    def test_env_through_submit_and_restart(self):
        def env_values(runtime):
            return [
                (e["name"], e.get("value"))
                if isinstance(e, dict)
                else (e.name, e.value)
                for e in runtime.container.env
            ]

        source = {
            "container": {
                "image": "busybox:1.36",
                "env": [
                    {
                        "name": "TOKEN",
                        "valueFrom": {"secretKeyRef": {"name": "s", "key": "token"}},
                    }
                ],
            },
            "env": {"TOKEN": "literal", "LEVEL": "debug"},
        }
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        assert run.kind == V1RunKind.JOB
        assert orjson_loads(run.raw_content) == source
        assert env_values(self.prepare(run)) == [
            ("TOKEN", "literal"),
            ("LEVEL", "debug"),
        ]

        override = {"env": {"LEVEL": "info"}}
        with patch("haupt.common.workers.send"):
            response = self.client.post(
                f"{self.url}{run.uuid.hex}/restart/",
                {"content": orjson_dumps(override)},
            )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        restarted = Run.objects.get(uuid=response.data["uuid"])
        assert orjson_loads(restarted.raw_content) == source
        assert env_values(self.prepare(restarted)) == [
            ("TOKEN", "literal"),
            ("LEVEL", "info"),
        ]

    def test_resources_through_submit_and_restart(self):
        source = {
            "container": {"image": "busybox:1.36"},
            "resources": {"cpu": "1..2", "gpu": 1},
        }
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        assert run.kind == V1RunKind.JOB
        assert orjson_loads(run.raw_content) == source
        # Resolution literal-evals plain strings, as for native resources: "1" -> 1.
        assert self.prepare(run).container.resources == {
            "requests": {"cpu": 1, "nvidia.com/gpu": 1},
            "limits": {"cpu": 2, "nvidia.com/gpu": 1},
        }

        override = {"resources": {"cpu": "4..8"}}
        with patch("haupt.common.workers.send"):
            response = self.client.post(
                f"{self.url}{run.uuid.hex}/restart/",
                {"content": orjson_dumps(override)},
            )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        restarted = Run.objects.get(uuid=response.data["uuid"])
        assert orjson_loads(restarted.raw_content) == source
        assert self.prepare(restarted).container.resources == {
            "requests": {"cpu": 4, "nvidia.com/gpu": 1},
            "limits": {"cpu": 8, "nvidia.com/gpu": 1},
        }

    def test_service_through_submit_and_restart(self):
        container = {"image": "busybox:1.36", "command": ["httpd"]}
        with_service = {"container": container, "service": {"ports": [8080]}}
        for source, override, kind in (
            # Adding a service section to a shortcut-only source selects a service.
            ({"container": container}, {"service": {"ports": [8080]}}, V1RunKind.JOB),
            # A null section keeps the existing one, so the run stays a service.
            (with_service, {"service": None}, V1RunKind.SERVICE),
        ):
            with self.subTest(source=source):
                response = self.client.post(self.url, {"content": orjson_dumps(source)})
                assert response.status_code == status.HTTP_201_CREATED, response.data
                run = Run.objects.get(uuid=response.data["uuid"])
                assert run.kind == kind
                assert self.prepare(run).kind == kind

                with patch("haupt.common.workers.send"):
                    response = self.client.post(
                        f"{self.url}{run.uuid.hex}/restart/",
                        {"content": orjson_dumps(override)},
                    )
                assert response.status_code == status.HTTP_201_CREATED, response.data
                restarted = Run.objects.get(uuid=response.data["uuid"])
                assert restarted.kind == V1RunKind.SERVICE
                assert orjson_loads(restarted.raw_content) == source
                runtime = self.prepare(restarted)
                assert runtime.kind == V1RunKind.SERVICE
                assert runtime.container.image == "busybox:1.36"
                assert runtime.ports == [8080]

    def test_dag_through_submit_and_restart(self):
        container = {"image": "busybox:1.36"}
        source = {
            "dag": {
                "concurrency": 2,
                "operations": [
                    {"name": "prepare", "container": container, "cmd": "echo prepare"},
                    {
                        "name": "train",
                        "dependencies": ["prepare"],
                        "container": container,
                        "cmd": "echo train",
                    },
                ],
            }
        }

        def restart(run, override):
            with patch("haupt.common.workers.send"):
                return self.client.post(
                    f"{self.url}{run.uuid.hex}/restart/",
                    {"content": orjson_dumps(override)},
                )

        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        assert run.kind == V1RunKind.DAG
        assert orjson_loads(run.raw_content) == source
        runtime = self.prepare(run)
        assert runtime.kind == V1RunKind.DAG
        assert runtime.concurrency == 2
        children = {child.name: child for child in run.pipeline_runs.all()}
        assert set(children) == {"prepare", "train"}
        for name, child in children.items():
            assert read_polyaxonfile(child.raw_content).name == name

        response = restart(run, {"dag": {"concurrency": 4}})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        restarted = Run.objects.get(uuid=response.data["uuid"])
        assert restarted.kind == V1RunKind.DAG
        assert orjson_loads(restarted.raw_content) == source
        assert self.prepare(restarted).concurrency == 4

        # An existing job is never converted to a DAG.
        content = orjson_dumps({"run": {"kind": "job", "container": container}})
        response = self.client.post(self.url, {"content": content})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        job = Run.objects.get(uuid=response.data["uuid"])
        runs = Run.objects.count()
        response = restart(job, {"dag": {}})
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert "requires a dag runtime" in str(response.data)
        assert Run.objects.count() == runs

    def test_run_patch_override_on_a_shortcut_runtime(self):
        source = {
            "container": {"image": "busybox:1.36", "command": ["httpd"]},
            "service": {"ports": [8080]},
            "runPatch": {"rewritePath": True},
        }
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        assert self.prepare(run).rewrite_path is True

        with patch("haupt.common.workers.send"):
            response = self.client.post(
                f"{self.url}{run.uuid.hex}/restart/",
                {"content": orjson_dumps({"runPatch": {"replicas": 2}})},
            )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        restarted = Run.objects.get(uuid=response.data["uuid"])
        assert orjson_loads(restarted.raw_content) == source
        runtime = self.prepare(restarted)
        assert runtime.rewrite_path is True
        assert runtime.replicas == 2

    def test_runtime_fields_through_submit_and_restart(self):
        source = {
            "container": {"image": "busybox:1.36"},
            "environment": {"nodeSelector": {"pool": "workers"}},
            "init": [{"container": {"name": "setup", "image": "busybox:1.36"}}],
            "sidecars": [{"name": "metrics", "image": "busybox:1.36"}],
            "volumes": [{"name": "scratch", "emptyDir": {}}],
        }
        response = self.client.post(self.url, {"content": orjson_dumps(source)})
        assert response.status_code == status.HTTP_201_CREATED, response.data
        run = Run.objects.get(uuid=response.data["uuid"])
        assert run.kind == V1RunKind.JOB
        assert orjson_loads(run.raw_content) == source
        runtime = self.prepare(run)
        assert runtime.environment.node_selector == {"pool": "workers"}
        assert [init.container.name for init in runtime.init] == ["setup"]
        assert [sidecar.name for sidecar in runtime.sidecars] == ["metrics"]
        assert [volume.name for volume in runtime.volumes] == ["scratch"]

        # An invalid override is a validation error, not a server error.
        runs = Run.objects.count()
        with patch("haupt.common.workers.send"):
            response = self.client.post(
                f"{self.url}{run.uuid.hex}/restart/",
                {"content": orjson_dumps({"sidecars": True})},
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert Run.objects.count() == runs

        override = {"environment": {"nodeSelector": {"pool": "gpu"}}}
        with patch("haupt.common.workers.send"):
            response = self.client.post(
                f"{self.url}{run.uuid.hex}/restart/",
                {"content": orjson_dumps(override)},
            )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        restarted = Run.objects.get(uuid=response.data["uuid"])
        assert orjson_loads(restarted.raw_content) == source
        runtime = self.prepare(restarted)
        assert runtime.environment.node_selector == {"pool": "gpu"}
        assert [sidecar.name for sidecar in runtime.sidecars] == ["metrics"]
