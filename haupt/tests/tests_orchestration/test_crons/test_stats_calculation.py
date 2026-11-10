from datetime import timedelta
import pytest
from unittest.mock import patch

from clipped.utils.tz import now
from haupt.common.test_cases.base import PolyaxonBaseTest
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.models.project_stats import ProjectStats
from haupt.db.models.projects import Project
from haupt.db.models.runs import Run
from haupt.orchestration.crons.stats import CronsStatsManager
from haupt.orchestration.scheduler.manager import SchedulingManager
from polyaxon.schemas import LiveState


@pytest.mark.crons_mark
class TestStatsCalculation(PolyaxonBaseTest):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()

    def test_stats_calculation_projects(self):
        assert self.project.latest_stats is None
        with patch("haupt.common.workers.send") as mock_send:
            CronsStatsManager.stats_calculation_projects()

        assert mock_send.call_count == 1

        # Add a new project stats
        self.project.latest_stats = ProjectStats(project=self.project)
        self.project.latest_stats.save()
        self.project.save(update_fields=["latest_stats"])

        assert self.project.updated_at < self.project.latest_stats.updated_at
        with patch("haupt.common.workers.send") as mock_send:
            CronsStatsManager.stats_calculation_projects()

        assert mock_send.call_count == 0

        # Update project updated_at
        self.project.name = "new-name"
        self.project.save()

        assert self.project.updated_at > self.project.latest_stats.updated_at

        with patch("haupt.common.workers.send") as mock_send:
            CronsStatsManager.stats_calculation_projects()

        assert mock_send.call_count == 1

    def test_stats_calculation_projects_includes_archived(self):
        archived = ProjectFactory()
        archived.latest_stats = ProjectStats(project=archived)
        archived.latest_stats.save()
        archived.save(update_fields=["latest_stats"])
        deleting = ProjectFactory(live_state=LiveState.DELETION_PROGRESSING)

        # `self.project` has no snapshot, so both calls dispatch something
        with patch("haupt.common.workers.send"):
            project_ids = CronsStatsManager.stats_calculation_projects()
        assert archived.id not in project_ids
        assert deleting.id not in project_ids

        archived.archive()

        with patch("haupt.common.workers.send"):
            project_ids = CronsStatsManager.stats_calculation_projects()
        assert archived.id in project_ids
        assert deleting.id not in project_ids

    def _age(self, run_age: timedelta, snapshot_age: timedelta):
        current = now()
        Run.all.filter(project=self.project).update(
            created_at=current - run_age, updated_at=current - run_age
        )
        ProjectStats.objects.filter(id=self.project.latest_stats_id).update(
            updated_at=current - snapshot_age
        )
        Project.all.filter(id=self.project.id).update(
            updated_at=current - snapshot_age - timedelta(hours=1)
        )

    @staticmethod
    def _dispatch_count():
        with patch("haupt.common.workers.send") as mock_send:
            CronsStatsManager.stats_calculation_projects()
        return mock_send.call_count

    def test_stats_calculation_projects_rolling_window(self):
        self.project.latest_stats = ProjectStats(project=self.project)
        self.project.latest_stats.save()
        self.project.save(update_fields=["latest_stats"])
        RunFactory(project=self.project, duration=10)

        # The run is still inside the window
        self._age(run_age=timedelta(days=10), snapshot_age=timedelta(days=2))
        assert self._dispatch_count() == 0

        # The run left the window, but the snapshot is younger than a day
        self._age(run_age=timedelta(days=31), snapshot_age=timedelta(hours=12))
        assert self._dispatch_count() == 0

        # The run left the window and the snapshot is older than a day
        self._age(run_age=timedelta(days=31), snapshot_age=timedelta(days=2))
        assert self._dispatch_count() == 1

        SchedulingManager.stats_calculation_project(project_id=self.project.id)
        self.project.refresh_from_db()
        assert self.project.latest_stats.tracking_time["rolling"]["avg"] is None
        assert self._dispatch_count() == 0

        # Two days after the recompute, the window has moved past the run
        self._age(run_age=timedelta(days=33), snapshot_age=timedelta(days=2))
        assert self._dispatch_count() == 0
