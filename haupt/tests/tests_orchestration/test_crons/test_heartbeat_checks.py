import pytest

from mock import patch

from clipped.utils.tz import get_datetime_from_now

from haupt.common.test_cases.base import PolyaxonBaseTest
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.orchestration.crons.heartbeats import CronsHeartbeatManager
from polyaxon.schemas import V1RunKind, V1RunPending, V1Statuses


@pytest.mark.crons_mark
class TestHeartBeatCrons(PolyaxonBaseTest):
    def test_heartbeat_stale_uploads(self):
        project = ProjectFactory()

        # Run with pending=UPLOAD and status=CREATED (should be failed)
        run1 = RunFactory(project=project, kind=V1RunKind.JOB)
        run1.status = V1Statuses.CREATED
        run1.pending = V1RunPending.UPLOAD
        run1.save()

        # Run with pending=UPLOAD and status=COMPILED (should be failed)
        run2 = RunFactory(project=project, kind=V1RunKind.JOB)
        run2.status = V1Statuses.COMPILED
        run2.pending = V1RunPending.UPLOAD
        run2.save()

        # Run with pending=UPLOAD but status=RUNNING (should NOT be affected)
        run3 = RunFactory(project=project, kind=V1RunKind.JOB)
        run3.status = V1Statuses.RUNNING
        run3.pending = V1RunPending.UPLOAD
        run3.save()

        # Run with status=CREATED but no pending (should NOT be affected)
        run4 = RunFactory(project=project, kind=V1RunKind.JOB)

        # Run with pending=BUILD and status=CREATED (should NOT be affected)
        run5 = RunFactory(project=project, kind=V1RunKind.JOB)
        run5.status = V1Statuses.CREATED
        run5.pending = V1RunPending.BUILD
        run5.save()

        # Check with minutes=0 to catch all stale runs
        CronsHeartbeatManager.heartbeat_out_of_sync(stale_uploads_minutes=0)
        run1.refresh_from_db()
        run2.refresh_from_db()
        run3.refresh_from_db()
        run4.refresh_from_db()
        run5.refresh_from_db()

        assert run1.status == V1Statuses.FAILED
        assert run2.status == V1Statuses.FAILED
        assert run3.status == V1Statuses.RUNNING
        assert run4.status == V1Statuses.CREATED
        assert run5.status == V1Statuses.CREATED

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

    def test_heartbeat_warning_runs(self):
        project = ProjectFactory()

        # Run in WARNING status (should be stopped)
        run1 = RunFactory(project=project, kind=V1RunKind.JOB)
        run1.status = V1Statuses.WARNING
        run1.save()

        # Run in UNSCHEDULABLE status (should be stopped)
        run2 = RunFactory(project=project, kind=V1RunKind.JOB)
        run2.status = V1Statuses.UNSCHEDULABLE
        run2.save()

        # Run in UNKNOWN status (should be stopped)
        run3 = RunFactory(project=project, kind=V1RunKind.SERVICE)
        run3.status = V1Statuses.UNKNOWN
        run3.save()

        # Run in RUNNING status (should NOT be affected)
        run4 = RunFactory(project=project, kind=V1RunKind.JOB)
        run4.status = V1Statuses.RUNNING
        run4.save()

        # Run in FAILED status (should NOT be affected)
        run5 = RunFactory(project=project, kind=V1RunKind.JOB)
        run5.status = V1Statuses.FAILED
        run5.save()

        # Run in CREATED status (should NOT be affected)
        run6 = RunFactory(project=project, kind=V1RunKind.JOB)

        # Check with minutes=0 to catch all warning runs
        CronsHeartbeatManager.heartbeat_out_of_sync(
            stale_uploads_minutes=999, warning_runs_minutes=0
        )
        run1.refresh_from_db()
        run2.refresh_from_db()
        run3.refresh_from_db()
        run4.refresh_from_db()
        run5.refresh_from_db()
        run6.refresh_from_db()

        assert run1.status == V1Statuses.STOPPING
        assert run2.status == V1Statuses.STOPPING
        assert run3.status == V1Statuses.STOPPING
        assert run4.status == V1Statuses.RUNNING
        assert run5.status == V1Statuses.FAILED
        assert run6.status == V1Statuses.CREATED
