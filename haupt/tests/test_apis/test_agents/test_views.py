import datetime
import pytest

from unittest.mock import patch

from rest_framework import status

from django.test import override_settings
from django.utils.timezone import now

from haupt.apis.serializers.runs import RunDetailSerializer
from haupt.background.celeryp.tasks import CronsCeleryTasks
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.models.runs import Run
from polyaxon import _operations, settings
from polyaxon._connections import V1BucketConnection, V1Connection, V1ConnectionKind
from polyaxon._schemas.agent import AgentConfig
from polyaxon._utils.fqn_utils import get_run_instance
from polyaxon.api import API_V1
from polyaxon.schemas import LiveState, ManagedBy, V1Environment, V1RunKind, V1Statuses
from tests.base.case import BaseTest


@pytest.mark.agent_mark
class TestAgentStateViewV1(BaseTest):
    def setUp(self):
        super().setUp()
        settings.AGENT_CONFIG = AgentConfig(
            namespace="foo",
            artifacts_store=V1Connection(
                name="moo",
                kind=V1ConnectionKind.GCS,
                schema_=V1BucketConnection(bucket="gs//:foo"),
            ),
        )
        self.url = "/{}/orgs/default/agents/state/".format(
            API_V1,
        )

    def _assert_agent_state(self):
        project = ProjectFactory()
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data == {
            "status": V1Statuses.RUNNING,
            "live_state": LiveState.LIVE,
            "state": {
                V1Statuses.QUEUED: [],
                V1Statuses.STOPPING: [],
                "deleting": [],
                "checks": [],
                "full": False,
            },
        }

        # Runs without satisfying status
        run1 = RunFactory(
            project=project,
            user=self.user,
            kind=V1RunKind.JOB,
        )
        run1.managed_by = ManagedBy.AGENT
        run2 = RunFactory(
            project=project,
            user=self.user,
            kind=V1RunKind.JOB,
        )
        run2.managed_by = ManagedBy.AGENT
        run3 = RunFactory(
            project=project,
            user=self.user,
            kind=V1RunKind.SERVICE,
        )
        run3.managed_by = ManagedBy.AGENT
        run4 = RunFactory(
            project=project,
            user=self.user,
            kind=V1RunKind.SERVICE,
        )
        run4.managed_by = ManagedBy.AGENT
        Run.all.update(managed_by=ManagedBy.AGENT)

        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data == {
            "status": V1Statuses.RUNNING,
            "live_state": LiveState.LIVE,
            "state": {
                V1Statuses.QUEUED: [],
                V1Statuses.STOPPING: [],
                "deleting": [],
                "checks": [],
                "full": False,
            },
        }

        run1.status = V1Statuses.QUEUED
        run1.save()
        run2.status = V1Statuses.QUEUED
        run2.save()
        run3.status = V1Statuses.QUEUED
        run3.save()
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["state"]["full"] is False
        assert resp.data["state"]["deleting"] == []
        assert resp.data["state"]["checks"] == []
        assert set(resp.data["state"][V1Statuses.QUEUED]) == {
            (
                get_run_instance(project.owner.name, project.name, run1.uuid.hex),
                run1.runtime,
                run1.name,
                run1.content,
                None,
            ),
            (
                get_run_instance(project.owner.name, project.name, run2.uuid.hex),
                run2.runtime,
                run2.name,
                run2.content,
                None,
            ),
            (
                get_run_instance(project.owner.name, project.name, run3.uuid.hex),
                run3.runtime,
                run3.name,
                run3.content,
                None,
            ),
        }
        assert resp.data["state"][V1Statuses.STOPPING] == []
        run1.refresh_from_db()
        run2.refresh_from_db()
        run3.refresh_from_db()
        assert run1.status == V1Statuses.SCHEDULED
        assert run2.status == V1Statuses.SCHEDULED
        assert run3.status == V1Statuses.SCHEDULED
        run1.status = V1Statuses.QUEUED
        run1.save()
        run2.status = V1Statuses.QUEUED
        run2.save()

        run3.status = V1Statuses.STOPPING
        run3.save()
        run4.status = V1Statuses.STOPPING
        run4.save()
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["state"]["full"] is False
        assert resp.data["state"]["deleting"] == []
        assert resp.data["state"]["checks"] == []
        assert set(resp.data["state"][V1Statuses.QUEUED]) == {
            (
                get_run_instance(project.owner.name, project.name, run1.uuid.hex),
                run1.runtime,
                run1.name,
                run1.content,
                None,
            ),
            (
                get_run_instance(project.owner.name, project.name, run2.uuid.hex),
                run2.runtime,
                run2.name,
                run2.content,
                None,
            ),
        }
        assert set(resp.data["state"][V1Statuses.STOPPING]) == {
            (
                get_run_instance(project.owner.name, project.name, run3.uuid.hex),
                run3.runtime,
                None,
            ),
            (
                get_run_instance(project.owner.name, project.name, run4.uuid.hex),
                run4.runtime,
                None,
            ),
        }
        run1.refresh_from_db()
        run2.refresh_from_db()
        assert run1.status == V1Statuses.SCHEDULED
        assert run2.status == V1Statuses.SCHEDULED
        run1.status = V1Statuses.QUEUED
        run1.save()
        run2.status = V1Statuses.QUEUED
        run2.save()

        run1.status = V1Statuses.STOPPING
        run1.save()
        run2.status = V1Statuses.STOPPING
        run2.save()
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["state"]["full"] is False
        assert resp.data["state"][V1Statuses.QUEUED] == []
        assert resp.data["state"]["deleting"] == []
        assert resp.data["state"]["checks"] == []
        assert set(resp.data["state"][V1Statuses.STOPPING]) == {
            (
                get_run_instance(project.owner.name, project.name, run1.uuid.hex),
                run1.runtime,
                None,
            ),
            (
                get_run_instance(project.owner.name, project.name, run2.uuid.hex),
                run2.runtime,
                None,
            ),
            (
                get_run_instance(project.owner.name, project.name, run3.uuid.hex),
                run3.runtime,
                None,
            ),
            (
                get_run_instance(project.owner.name, project.name, run4.uuid.hex),
                run4.runtime,
                None,
            ),
        }

        # Trigger checks
        checked_at = now() - datetime.timedelta(hours=3)
        run1.checked_at = checked_at
        run1.status = V1Statuses.RUNNING
        run1.save()
        run2.checked_at = checked_at
        run2.status = V1Statuses.COMPILED
        run2.save()

        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["state"]["full"] is False
        assert resp.data["state"][V1Statuses.QUEUED] == []
        assert resp.data["state"]["deleting"] == []
        assert resp.data["state"]["checks"] == [
            (
                get_run_instance(project.owner.name, project.name, run1.uuid.hex),
                run1.runtime,
                None,
            ),
        ]
        assert set(resp.data["state"][V1Statuses.STOPPING]) == {
            (
                get_run_instance(project.owner.name, project.name, run3.uuid.hex),
                run3.runtime,
                None,
            ),
            (
                get_run_instance(project.owner.name, project.name, run4.uuid.hex),
                run4.runtime,
                None,
            ),
        }

        # Deleting
        run5 = RunFactory(
            project=project,
            user=self.user,
            kind=V1RunKind.SERVICE,
        )
        run5.managed_by = ManagedBy.AGENT
        run6 = RunFactory(
            project=project,
            user=self.user,
            kind=V1RunKind.JOB,
        )
        run6.managed_by = ManagedBy.AGENT
        Run.all.update(managed_by=ManagedBy.AGENT)

        run1.live_state = LiveState.DELETION_PROGRESSING
        run1.save()
        run2.live_state = LiveState.DELETION_PROGRESSING
        run2.status = V1Statuses.COMPILED
        run2.save()

        run5.live_state = LiveState.DELETION_PROGRESSING
        run5.status = V1Statuses.STOPPED
        run5.save()
        run6.live_state = LiveState.DELETION_PROGRESSING
        run6.status = V1Statuses.FAILED
        run6.save()

        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["state"]["full"] is False
        assert resp.data["state"][V1Statuses.QUEUED] == []
        assert resp.data["state"]["checks"] == []
        assert set(resp.data["state"]["deleting"]) == {
            (
                get_run_instance(project.owner.name, "agent", "agent"),
                V1RunKind.JOB,
                "cleaner",
                _operations.get_batch_cleaner_operation(
                    environment=V1Environment(),
                    connection=settings.AGENT_CONFIG.artifacts_store,
                    paths=[run5.uuid.hex, run6.uuid.hex],
                ).to_json(include_version=True),
                None,
            ),
            (
                get_run_instance(project.owner.name, project.name, run1.uuid.hex),
                run1.runtime,
                run1.name,
                None,
                None,
            ),
            (
                get_run_instance(project.owner.name, project.name, run2.uuid.hex),
                run2.runtime,
                run2.name,
                None,
                None,
            ),
        }
        assert set(resp.data["state"][V1Statuses.STOPPING]) == {
            (
                get_run_instance(project.owner.name, project.name, run3.uuid.hex),
                run3.runtime,
                None,
            ),
            (
                get_run_instance(project.owner.name, project.name, run4.uuid.hex),
                run4.runtime,
                None,
            ),
        }

    @override_settings(MIN_ARTIFACTS_DELETION_TIMEDELTA=-60)
    def test_agent_state(self):
        self._assert_agent_state()


@pytest.mark.agent_mark
class TestAgentCronViewV1(BaseTest):
    def setUp(self):
        self.url = "/{}/orgs/default/agents/cron/".format(
            API_V1,
        )

    @patch("haupt.common.workers.send")
    def test_agent_cron(self, workers_send):
        resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 8
        assert {c[0][0] for c in workers_send.call_args_list} == {
            CronsCeleryTasks.HEARTBEAT_OUT_OF_SYNC_SCHEDULES,
            CronsCeleryTasks.HEARTBEAT_STOPPING_RUNS,
            CronsCeleryTasks.HEARTBEAT_PROJECT_LAST_UPDATED,
            CronsCeleryTasks.STATS_CALCULATION_PROJECTS,
            CronsCeleryTasks.DELETE_ARCHIVED_PROJECTS,
            CronsCeleryTasks.DELETE_IN_PROGRESS_PROJECTS,
            CronsCeleryTasks.DELETE_ARCHIVED_RUNS,
            CronsCeleryTasks.DELETE_IN_PROGRESS_RUNS,
        }


@pytest.mark.agent_mark
class TestAgentRunDetailViewV1(BaseTest):
    model_class = Run
    factory_class = RunFactory
    serializer_class = RunDetailSerializer

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()
        self.object = self.factory_class(
            user=self.user,
            project=self.project,
            content="test",
            raw_content="test",
            managed_by=ManagedBy.AGENT,
        )
        self.url = "/{}/orgs/default/runs/{}".format(API_V1, self.object.uuid.hex)

    def test_get(self):
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        self.object.refresh_from_db()
        expected = self.serializer_class(self.object).data
        assert resp.data == expected
