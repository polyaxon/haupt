from clipped.utils.tz import get_datetime_from_now

from django.test import TestCase

from haupt.db.factories.projects import ProjectFactory, ProjectVersionFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.factories.users import UserFactory
from haupt.db.managers.deleted import ArchivedManager, LiveManager
from haupt.db.managers.projects import (
    update_project_based_on_last_runs,
    update_project_based_on_last_versions,
)
from haupt.db.models.projects import Project


class TestProjectModel(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()

    def test_managers(self):
        assert isinstance(Project.objects, LiveManager)
        assert isinstance(Project.archived, ArchivedManager)

    def test_update_project_based_on_last_runs(self):
        current_project_updated_at = self.project.updated_at
        time_threshold = get_datetime_from_now(days=0, minutes=2)
        project_threshold = get_datetime_from_now(days=0, seconds=15)

        update_project_based_on_last_runs(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        self.project.refresh_from_db()
        assert self.project.updated_at == current_project_updated_at

        # Add a new run
        RunFactory(project=self.project)

        update_project_based_on_last_runs(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        self.project.refresh_from_db()
        assert self.project.updated_at == current_project_updated_at

        # Update intervals to trigger update
        time_threshold = get_datetime_from_now(days=0, minutes=0)
        project_threshold = get_datetime_from_now(days=0, seconds=0)

        update_project_based_on_last_runs(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        assert self.project.updated_at >= current_project_updated_at

    def test_update_project_based_on_last_versions(self):
        current_project_updated_at = self.project.updated_at
        time_threshold = get_datetime_from_now(days=0, minutes=2)
        project_threshold = get_datetime_from_now(days=0, seconds=15)

        update_project_based_on_last_versions(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        self.project.refresh_from_db()
        assert self.project.updated_at == current_project_updated_at

        # Add a new version
        ProjectVersionFactory(project=self.project)

        update_project_based_on_last_versions(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        self.project.refresh_from_db()
        assert self.project.updated_at == current_project_updated_at

        # Update intervals to trigger update
        time_threshold = get_datetime_from_now(days=0, minutes=0)
        project_threshold = get_datetime_from_now(days=0, seconds=0)

        update_project_based_on_last_versions(
            last_created_at_threshold=time_threshold,
            last_updated_at_threshold=project_threshold,
        )
        assert self.project.updated_at >= current_project_updated_at
