from flaky import flaky

from clipped.utils.tz import get_datetime_from_now

from django.test import TestCase

from haupt.db.factories.projects import ProjectFactory, ProjectVersionFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.managers.deleted import ArchivedManager, LiveManager
from haupt.db.managers.projects import update_project_based_on_last_updated_entities
from haupt.db.managers.stats import (
    collect_project_run_count_stats,
    collect_project_run_duration_stats,
    collect_project_run_status_stats,
    collect_project_version_stats,
)
from haupt.db.models.project_stats import ProjectStats
from haupt.db.models.projects import Project
from polyaxon.lifecycle import LiveState, V1ProjectVersionKind, V1Statuses


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

    @flaky(max_runs=3)
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
        run_count = collect_project_run_count_stats(self.project)
        assert run_count == {}

        # Add a new runs
        RunFactory(project=self.project)
        RunFactory(project=self.project)
        RunFactory(project=self.project, live_state=LiveState.ARCHIVED)
        RunFactory(project=self.project, live_state=LiveState.DELETION_PROGRESSING)

        run_count = collect_project_run_count_stats(self.project)
        assert run_count == {
            LiveState.LIVE.value: 2,
            LiveState.ARCHIVED.value: 1,
            LiveState.DELETION_PROGRESSING.value: 1,
        }

    def test_collect_project_run_status_stats(self):
        run_count = collect_project_run_status_stats(self.project)
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

        run_count = collect_project_run_status_stats(self.project)
        assert run_count == {
            V1Statuses.RUNNING.value: 2,
            V1Statuses.STARTING.value: 1,
        }

    def test_collect_project_run_duration_stats(self):
        run_duration = collect_project_run_duration_stats(self.project)
        assert run_duration == {}

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

        run_duration = collect_project_run_duration_stats(self.project)
        assert run_duration == {
            LiveState.LIVE.value: 28,
            LiveState.ARCHIVED.value: 24,
            LiveState.DELETION_PROGRESSING.value: 3,
        }

    def test_collect_project_version_stats(self):
        version_count = collect_project_version_stats(self.project)
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

        version_count = collect_project_version_stats(self.project)
        assert version_count == {
            V1ProjectVersionKind.COMPONENT.value: 4,
            V1ProjectVersionKind.MODEL.value: 2,
            V1ProjectVersionKind.ARTIFACT.value: 3,
        }
