from datetime import timedelta
import pytest

from clipped.utils.tz import get_datetime_from_now

from django.test import TestCase
from django.utils.timezone import now


from haupt.db.factories.projects import ProjectFactory, ProjectVersionFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.managers.deleted import ArchivedManager, LiveManager
from haupt.db.managers.projects import update_project_based_on_last_updated_entities
from haupt.db.managers.stats import (
    collect_entity_run_stats,
    collect_entity_run_status_stats,
    collect_project_version_stats,
)
from haupt.db.models.project_stats import ProjectStats
from haupt.db.models.projects import Project
from polyaxon.schemas import LiveState, V1ProjectVersionKind, V1Statuses


class TestProjectModel(TestCase):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()

    def test_managers(self):
        assert isinstance(Project.objects, LiveManager)
        assert isinstance(Project.archived, ArchivedManager)

    def test_update_project_based_on_last_runs(self):
        current_project_updated_at = self.project.updated_at
        time_threshold = get_datetime_from_now(days=0, minutes=2)
        project_threshold = get_datetime_from_now(days=0, seconds=15)

        update_project_based_on_last_updated_entities(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        self.project.refresh_from_db()
        assert self.project.updated_at == current_project_updated_at

        # Add a new run
        run = RunFactory(project=self.project)

        update_project_based_on_last_updated_entities(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        self.project.refresh_from_db()
        assert self.project.updated_at == current_project_updated_at

        # Update intervals to trigger update
        time_threshold = get_datetime_from_now(days=0, minutes=0)
        project_threshold = get_datetime_from_now(days=0, seconds=0)

        update_project_based_on_last_updated_entities(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        assert self.project.updated_at >= current_project_updated_at

        # Update the last checkpoint
        current_project_updated_at = self.project.updated_at

        update_project_based_on_last_updated_entities(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        self.project.refresh_from_db()
        assert self.project.updated_at == current_project_updated_at

        # Archive run
        run.archive()
        update_project_based_on_last_updated_entities(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        self.project.refresh_from_db()
        assert self.project.updated_at >= current_project_updated_at

        # Update the last checkpoint
        current_project_updated_at = self.project.updated_at

        update_project_based_on_last_updated_entities(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        self.project.refresh_from_db()
        assert self.project.updated_at == current_project_updated_at

        # Delete run
        run.delete_in_progress()
        update_project_based_on_last_updated_entities(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        self.project.refresh_from_db()
        assert self.project.updated_at >= current_project_updated_at

    def test_update_project_based_on_last_versions(self):
        current_project_updated_at = self.project.updated_at
        time_threshold = get_datetime_from_now(days=0, minutes=2)
        project_threshold = get_datetime_from_now(days=0, seconds=15)

        update_project_based_on_last_updated_entities(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        self.project.refresh_from_db()
        assert self.project.updated_at == current_project_updated_at

        # Add a new version
        ProjectVersionFactory(project=self.project)

        update_project_based_on_last_updated_entities(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        self.project.refresh_from_db()
        assert self.project.updated_at == current_project_updated_at

        # Update intervals to trigger update
        time_threshold = get_datetime_from_now(days=0, minutes=0)
        project_threshold = get_datetime_from_now(days=0, seconds=0)

        update_project_based_on_last_updated_entities(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        assert self.project.updated_at >= current_project_updated_at

    @pytest.mark.flaky(max_runs=3)
    def test_project_stats_created_at(self):
        stats = ProjectStats(project=self.project)
        stats.save()

        assert stats.created_at.second == 0
        assert stats.created_at.minute == 0
        assert stats.created_at.hour != 0

        assert stats.updated_at.second != 0
        assert stats.updated_at.minute != 0
        assert stats.updated_at.hour != 0

    def test_collect_project_run_count_stats(self):
        run_count = collect_entity_run_stats(project=self.project).run_count
        assert run_count == {}

        # Add a new runs
        RunFactory(project=self.project)
        RunFactory(project=self.project)
        RunFactory(project=self.project, live_state=LiveState.ARCHIVED)
        RunFactory(project=self.project, live_state=LiveState.DELETION_PROGRESSING)

        run_count = collect_entity_run_stats(project=self.project).run_count
        assert run_count == {
            LiveState.LIVE.value: 2,
            LiveState.ARCHIVED.value: 1,
            LiveState.DELETION_PROGRESSING.value: 1,
        }

    def test_collect_entity_run_status_stats(self):
        run_count = collect_entity_run_status_stats(project=self.project)
        assert run_count == {}

        # Add a new runs
        RunFactory(project=self.project, status=V1Statuses.RUNNING)
        RunFactory(project=self.project, status=V1Statuses.RUNNING)
        RunFactory(
            project=self.project,
            live_state=LiveState.ARCHIVED,
            status=V1Statuses.STOPPED,
        )
        RunFactory(
            project=self.project,
            status=V1Statuses.STARTING,
        )

        run_count = collect_entity_run_status_stats(project=self.project)
        assert run_count == {
            V1Statuses.RUNNING.value: 2,
            V1Statuses.STARTING.value: 1,
        }

    def test_collect_project_run_duration_stats(self):
        run_duration = collect_entity_run_stats(project=self.project).tracking_time
        # Now includes rolling stats with None values when no data
        assert run_duration == {"rolling": {"avg": None, "min": None, "max": None}}

        # Add a new runs
        RunFactory(project=self.project, duration=12)
        RunFactory(project=self.project, duration=16)
        RunFactory(project=self.project, duration=12, live_state=LiveState.ARCHIVED)
        RunFactory(project=self.project, duration=12, live_state=LiveState.ARCHIVED)
        RunFactory(
            project=self.project, duration=2, live_state=LiveState.DELETION_PROGRESSING
        )
        RunFactory(
            project=self.project, duration=1, live_state=LiveState.DELETION_PROGRESSING
        )

        run_duration = collect_entity_run_stats(project=self.project).tracking_time
        # Check base stats
        assert run_duration[LiveState.LIVE.value] == 28
        assert run_duration[LiveState.ARCHIVED.value] == 24
        assert run_duration[LiveState.DELETION_PROGRESSING.value] == 3
        # Rolling stats will be calculated from runs in the last hour
        assert "rolling" in run_duration

    def test_collect_project_version_stats(self):
        version_count = collect_project_version_stats(project=self.project)
        assert version_count == {}

        # Add a new versions
        ProjectVersionFactory(project=self.project, kind=V1ProjectVersionKind.COMPONENT)
        ProjectVersionFactory(project=self.project, kind=V1ProjectVersionKind.COMPONENT)
        ProjectVersionFactory(project=self.project, kind=V1ProjectVersionKind.COMPONENT)
        ProjectVersionFactory(project=self.project, kind=V1ProjectVersionKind.COMPONENT)
        ProjectVersionFactory(project=self.project, kind=V1ProjectVersionKind.MODEL)
        ProjectVersionFactory(project=self.project, kind=V1ProjectVersionKind.MODEL)
        ProjectVersionFactory(project=self.project, kind=V1ProjectVersionKind.ARTIFACT)
        ProjectVersionFactory(project=self.project, kind=V1ProjectVersionKind.ARTIFACT)
        ProjectVersionFactory(project=self.project, kind=V1ProjectVersionKind.ARTIFACT)

        version_count = collect_project_version_stats(project=self.project)
        assert version_count == {
            V1ProjectVersionKind.COMPONENT.value: 4,
            V1ProjectVersionKind.MODEL.value: 2,
            V1ProjectVersionKind.ARTIFACT.value: 3,
        }

    def test_collect_entity_run_rolling_stats(self):
        """Test that rolling stats are properly calculated for recent runs"""
        # Test empty rolling stats
        run_stats = collect_entity_run_stats(project=self.project)
        assert run_stats.tracking_time["rolling"]["avg"] is None
        assert run_stats.tracking_time["rolling"]["min"] is None
        assert run_stats.tracking_time["rolling"]["max"] is None
        assert run_stats.wait_time["rolling"]["avg"] is None
        assert run_stats.wait_time["rolling"]["min"] is None
        assert run_stats.wait_time["rolling"]["max"] is None

        # Create runs with specific timestamps
        recent_time = now() - timedelta(minutes=30)
        old_time = now() - timedelta(days=31)  # Outside the 30-day rolling window

        # Recent runs (should be included in rolling stats)
        run1 = RunFactory(project=self.project, duration=10, wait_time=5)
        run2 = RunFactory(project=self.project, duration=20, wait_time=10)
        run3 = RunFactory(project=self.project, duration=30, wait_time=15)

        # Update created_at to be recent
        from haupt.db.models.runs import Run

        Run.objects.filter(id__in=[run1.id, run2.id, run3.id]).update(
            created_at=recent_time
        )

        # Old run (should NOT be included in rolling stats)
        run4 = RunFactory(project=self.project, duration=100, wait_time=50)
        Run.objects.filter(id=run4.id).update(created_at=old_time)

        # Get stats again
        run_stats = collect_entity_run_stats(project=self.project)

        # Check rolling stats only include recent runs
        assert run_stats.tracking_time["rolling"]["avg"] == 20  # (10+20+30)/3
        assert run_stats.tracking_time["rolling"]["min"] == 10
        assert run_stats.tracking_time["rolling"]["max"] == 30

        assert run_stats.wait_time["rolling"]["avg"] == 10  # (5+10+15)/3
        assert run_stats.wait_time["rolling"]["min"] == 5
        assert run_stats.wait_time["rolling"]["max"] == 15

        # Check that all runs are in the base stats
        assert run_stats.tracking_time[LiveState.LIVE.value] == 160  # 10+20+30+100

    def test_collect_entity_run_resources_with_rolling_stats(self):
        """Test that resources field includes rolling stats for cpu, memory, gpu, cost"""
        from django.utils.timezone import now
        from datetime import timedelta

        # Test empty resources
        run_stats = collect_entity_run_stats(project=self.project)
        assert "cpu" in run_stats.resources
        assert "memory" in run_stats.resources
        assert "gpu" in run_stats.resources
        assert "cost" in run_stats.resources
        assert "custom" in run_stats.resources

        # Each resource should have rolling stats
        for resource in ["cpu", "memory", "gpu", "cost", "custom"]:
            assert "rolling" in run_stats.resources[resource]
            assert run_stats.resources[resource]["rolling"]["avg"] is None
            assert run_stats.resources[resource]["rolling"]["min"] is None
            assert run_stats.resources[resource]["rolling"]["max"] is None

        # Create runs with resources in the last hour
        recent_time = now() - timedelta(minutes=30)

        run1 = RunFactory(
            project=self.project, cpu=1.0, memory=1024, gpu=0.5, cost=10.0
        )
        run2 = RunFactory(
            project=self.project, cpu=2.0, memory=2048, gpu=1.0, cost=20.0
        )
        run3 = RunFactory(
            project=self.project, cpu=4.0, memory=4096, gpu=2.0, cost=40.0
        )

        # Update created_at to be recent
        from haupt.db.models.runs import Run

        Run.objects.filter(id__in=[run1.id, run2.id, run3.id]).update(
            created_at=recent_time
        )

        # Get stats again
        run_stats = collect_entity_run_stats(project=self.project)

        # Check CPU rolling stats
        assert run_stats.resources["cpu"]["rolling"]["avg"] == pytest.approx(
            2.333, rel=0.01
        )  # (1+2+4)/3
        assert run_stats.resources["cpu"]["rolling"]["min"] == 1.0
        assert run_stats.resources["cpu"]["rolling"]["max"] == 4.0

        # Check Memory rolling stats
        assert run_stats.resources["memory"]["rolling"]["avg"] == pytest.approx(
            2389.333, rel=1
        )  # (1024+2048+4096)/3
        assert run_stats.resources["memory"]["rolling"]["min"] == 1024
        assert run_stats.resources["memory"]["rolling"]["max"] == 4096

        # Check GPU rolling stats
        assert run_stats.resources["gpu"]["rolling"]["avg"] == pytest.approx(
            1.166, rel=0.01
        )  # (0.5+1+2)/3
        assert run_stats.resources["gpu"]["rolling"]["min"] == 0.5
        assert run_stats.resources["gpu"]["rolling"]["max"] == 2.0

        # Check Cost rolling stats
        assert run_stats.resources["cost"]["rolling"]["avg"] == pytest.approx(
            23.333, rel=0.01
        )  # (10+20+40)/3
        assert run_stats.resources["cost"]["rolling"]["min"] == 10.0
        assert run_stats.resources["cost"]["rolling"]["max"] == 40.0
