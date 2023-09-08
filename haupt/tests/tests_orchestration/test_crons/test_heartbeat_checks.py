import pytest

from mock import patch

from clipped.utils.tz import get_datetime_from_now

from haupt.common.test_cases.base import PolyaxonBaseTest
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.orchestration.crons.heartbeats import CronsHeartbeatManager
from polyaxon.lifecycle import V1Statuses
from polyaxon.polyflow import V1RunKind


@pytest.mark.crons_mark
class TestHeartBeatCrons(PolyaxonBaseTest):
    def test_heartbeat_out_of_sync_schedules(self):
        project = ProjectFactory()
        run1 = RunFactory(project=project, kind=V1RunKind.SCHEDULE)
        run1.status = V1Statuses.RUNNING
        run1.save()
        run2 = RunFactory(project=project, kind=V1RunKind.JOB, pipeline=run1)
        run2.status = V1Statuses.STOPPED
        run2.finished_at = get_datetime_from_now(days=0, minutes=0)
        run2.save()

        with patch("haupt.common.workers.send") as mock_send:
            CronsHeartbeatManager.heartbeat_out_of_sync_schedules()

        assert mock_send.call_count == 0

        run2.finished_at = get_datetime_from_now(days=0, minutes=10)
        run2.save()

        with patch("haupt.common.workers.send") as mock_send:
            CronsHeartbeatManager.heartbeat_out_of_sync_schedules()

        assert mock_send.call_count == 1

        run2.status = V1Statuses.RUNNING
        run2.save()

        with patch("haupt.common.workers.send") as mock_send:
            CronsHeartbeatManager.heartbeat_out_of_sync_schedules()

        assert mock_send.call_count == 0

        run2.status = V1Statuses.FAILED
        run2.save()

        with patch("haupt.common.workers.send") as mock_send:
            CronsHeartbeatManager.heartbeat_out_of_sync_schedules()

        assert mock_send.call_count == 1

        run1.status = V1Statuses.STOPPED
        run1.save()

        with patch("haupt.common.workers.send") as mock_send:
            CronsHeartbeatManager.heartbeat_out_of_sync_schedules()

        assert mock_send.call_count == 0

    def test_heartbeat_stopping_runs(self):
        project = ProjectFactory()
        run1 = RunFactory(project=project, kind=V1RunKind.JOB)
        run1.status = V1Statuses.SCHEDULED
        run1.save()
        run2 = RunFactory(project=project, kind=V1RunKind.JOB)
        run3 = RunFactory(project=project, kind=V1RunKind.SERVICE)
        run3.status = V1Statuses.FAILED
        run3.save()
        run4 = RunFactory(project=project, kind=V1RunKind.DAG)
        run4.status = V1Statuses.STARTING
        run4.save()
        run5 = RunFactory(
            project=project,
            pipeline=run4,
            controller=run4,
            kind=V1RunKind.SERVICE,
        )
        run5.status = V1Statuses.RUNNING
        run5.save()

        # Check
        CronsHeartbeatManager.heartbeat_stopping_runs(minutes=0)
        run1.refresh_from_db()
        run2.refresh_from_db()
        run3.refresh_from_db()
        run4.refresh_from_db()
        run5.refresh_from_db()

        assert run1.status == V1Statuses.SCHEDULED
        assert run2.status == V1Statuses.CREATED
        assert run3.status == V1Statuses.FAILED
        assert run4.status == V1Statuses.STARTING
        assert run5.status == V1Statuses.RUNNING

        run1.status = V1Statuses.STOPPING
        run1.save()
        run4.status = V1Statuses.STOPPING
        run4.save()

        # Check
        CronsHeartbeatManager.heartbeat_stopping_runs(minutes=0)
        run1.refresh_from_db()
        run2.refresh_from_db()
        run3.refresh_from_db()
        run4.refresh_from_db()
        run5.refresh_from_db()

        assert run1.status == V1Statuses.STOPPED
        assert run2.status == V1Statuses.CREATED
        assert run3.status == V1Statuses.FAILED
        assert run4.status == V1Statuses.STOPPING
        assert run5.status == V1Statuses.RUNNING

        run5.status = V1Statuses.STOPPING
        run5.save()

        # Check
        CronsHeartbeatManager.heartbeat_stopping_runs(minutes=0)
        run1.refresh_from_db()
        run2.refresh_from_db()
        run3.refresh_from_db()
        run4.refresh_from_db()
        run5.refresh_from_db()

        assert run1.status == V1Statuses.STOPPED
        assert run2.status == V1Statuses.CREATED
        assert run3.status == V1Statuses.FAILED
        assert run4.status == V1Statuses.STOPPED
        assert run5.status == V1Statuses.STOPPED
