from datetime import timedelta
from unittest.mock import patch

import pytest

from django.utils.timezone import now

from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.common.test_cases.base import PolyaxonBaseTest
from haupt.db.factories.projects import ProjectFactory
from haupt.db.managers.cleaning import compact_owner_stats
from haupt.db.models.project_stats import ProjectStats
from haupt.orchestration.crons.cleaning import CronsCleaningManager
from haupt.orchestration.scheduler.manager import SchedulingManager


@pytest.mark.crons_mark
class TestCleanStatsProjectsFanout(PolyaxonBaseTest):
    def test_fanout_enqueues_one_task_per_project(self):
        projects = [ProjectFactory() for _ in range(3)]

        with patch("haupt.common.workers.send") as mock_send:
            CronsCleaningManager.clean_stats_projects()

        assert mock_send.call_count == len(projects)
        enqueued_ids = {
            call.kwargs.get("kwargs", {}).get("project_id")
            or call.args[1]["project_id"]
            for call in mock_send.call_args_list
        }
        assert enqueued_ids == {p.id for p in projects}
        assert all(
            call.args[0] == SchedulerCeleryTasks.CLEAN_STATS_PROJECT
            for call in mock_send.call_args_list
        )


@pytest.mark.crons_mark
class TestCleanStatsProject(PolyaxonBaseTest):
    # Use tight retention windows so tests don't manipulate year-old timestamps.
    RAW_DAYS = 1
    HOURLY_DAYS = 3

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()

    @staticmethod
    def _make(project, created_at):
        stats = ProjectStats.objects.create(project=project)
        ProjectStats.objects.filter(id=stats.id).update(created_at=created_at)
        stats.refresh_from_db()
        return stats

    def _compact(self, project_id):
        compact_owner_stats(
            stats_model=ProjectStats,
            obj_fk="project",
            obj_id=project_id,
            pinned_id=None,
            raw_retention_days=self.RAW_DAYS,
            hourly_retention_days=self.HOURLY_DAYS,
        )

    def test_clean_stats_project_missing_is_noop(self):
        SchedulingManager.clean_stats_project(project_id=999_999)

    def test_raw_tier_is_untouched(self):
        base = now() - timedelta(hours=1)
        rows = [self._make(self.project, base + timedelta(minutes=5 * i)) for i in range(6)]

        self._compact(self.project.id)

        assert ProjectStats.objects.filter(id__in=[r.id for r in rows]).count() == len(rows)

    def test_hourly_tier_compacts_to_one_per_hour(self):
        base = now() - timedelta(days=self.RAW_DAYS + 1)
        base = base.replace(minute=0, second=0, microsecond=0)
        rows = [self._make(self.project, base + timedelta(minutes=5 * i)) for i in range(12)]

        self._compact(self.project.id)

        surviving = ProjectStats.objects.filter(id__in=[r.id for r in rows])
        assert surviving.count() == 1
        assert surviving.first().id == max(r.id for r in rows)

    def test_daily_tier_compacts_to_one_per_day(self):
        base = now() - timedelta(days=self.HOURLY_DAYS + 1)
        base = base.replace(hour=0, minute=0, second=0, microsecond=0)
        rows = [self._make(self.project, base + timedelta(hours=i)) for i in range(24)]

        self._compact(self.project.id)

        surviving = ProjectStats.objects.filter(id__in=[r.id for r in rows])
        assert surviving.count() == 1
        assert surviving.first().id == max(r.id for r in rows)

    def test_other_projects_untouched(self):
        other = ProjectFactory()
        base = now() - timedelta(days=self.RAW_DAYS + 1)
        base = base.replace(minute=0, second=0, microsecond=0)
        for i in range(3):
            self._make(self.project, base + timedelta(minutes=5 * i))
            self._make(other, base + timedelta(minutes=5 * i))

        self._compact(self.project.id)

        assert ProjectStats.objects.filter(project=self.project).count() == 1
        assert ProjectStats.objects.filter(project=other).count() == 3

    def test_latest_stats_pointer_preserved(self):
        base = now() - timedelta(days=self.HOURLY_DAYS + 1)
        base = base.replace(hour=0, minute=0, second=0, microsecond=0)
        pinned = self._make(self.project, base)
        for i in range(1, 4):
            self._make(self.project, base + timedelta(hours=i))

        compact_owner_stats(
            stats_model=ProjectStats,
            obj_fk="project",
            obj_id=self.project.id,
            pinned_id=pinned.id,
            raw_retention_days=self.RAW_DAYS,
            hourly_retention_days=self.HOURLY_DAYS,
        )

        assert ProjectStats.objects.filter(id=pinned.id).exists()
