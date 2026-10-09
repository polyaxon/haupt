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
