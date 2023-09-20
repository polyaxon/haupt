import pytest

from unittest.mock import patch

from haupt.common.test_cases.base import PolyaxonBaseTest
from haupt.db.factories.projects import ProjectFactory, ProjectVersionFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.models.project_versions import ProjectVersion
from haupt.db.models.projects import Project
from haupt.db.models.runs import Run
from haupt.orchestration.crons.deletion import CronsDeletionManager
from polyaxon.schemas import V1ProjectVersionKind, V1RunKind, V1Statuses


@pytest.mark.crons_mark
class TestDeletionCrons(PolyaxonBaseTest):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()

    def test_delete_archived_projects(self):
        project1 = ProjectFactory()
        RunFactory(project=project1)
        ProjectVersionFactory(project=project1, kind=V1ProjectVersionKind.COMPONENT)
        ProjectVersionFactory(project=project1, kind=V1ProjectVersionKind.MODEL)
        ProjectVersionFactory(project=project1, kind=V1ProjectVersionKind.ARTIFACT)
        project1.archive()
        project2 = ProjectFactory()
        experiment2 = RunFactory(project=project2)
        ProjectVersionFactory(project=project2, kind=V1ProjectVersionKind.COMPONENT)
        ProjectVersionFactory(project=project2, kind=V1ProjectVersionKind.MODEL)
        ProjectVersionFactory(project=project2, kind=V1ProjectVersionKind.ARTIFACT)
        experiment2.archive()

        assert Project.all.count() == 3
        assert Project.archived.count() == 1
        assert Run.all.count() == 2
        assert Run.archived.count() == 1
        assert ProjectVersion.objects.count() == 6

        with self.settings(CLEANING_INTERVALS_ARCHIVES=-10):
            with patch("haupt.common.workers.send") as mock_send:
                CronsDeletionManager.delete_archived_projects()

        # Deletes only one project
        assert mock_send.call_count == 1
        assert Project.all.count() == 3  # Deletion is done remotely
        assert Project.archived.count() == 1
        # Although the other experiment is archived it's not deleted because of project2
        assert Run.all.count() == 2  # Deletion is done remotely
        assert Run.archived.count() == 1
        assert ProjectVersion.objects.count() == 6

    def test_delete_archived_runs(self):
        project1 = ProjectFactory()
        RunFactory(project=project1)
        project1.archive()
        project2 = ProjectFactory()
        run2 = RunFactory(project=project2)
        run2.archive()
        group1 = RunFactory(project=self.project)
        run3 = RunFactory(project=project2, pipeline=group1)
        run3.archive()

        assert Run.all.count() == 4

        with self.settings(CLEANING_INTERVALS_ARCHIVES=-10):
            with patch("haupt.common.workers.send") as mock_send:
                CronsDeletionManager.delete_archived_runs()

        # Although the other run is archived it's not deleted because of project1 and group1
        assert mock_send.call_count == 2
        assert Run.all.count() == 4  # Deletion is done remotely

    def test_delete_in_progress_runs(self):
        group1 = RunFactory(project=self.project, kind=V1RunKind.DAG)
        RunFactory(project=self.project, pipeline=group1, kind=V1RunKind.JOB)

        assert Run.all.count() == 2
        assert Run.all.filter(deleted_at__isnull=True).count() == 2

        group1.delete_in_progress(set_deleted_at=False)

        assert Run.all.count() == 2
        assert Run.all.filter(deleted_at__isnull=True).count() == 2

        group2 = RunFactory(project=self.project, kind=V1RunKind.DAG)

        assert Run.all.count() == 3
        assert Run.all.filter(deleted_at__isnull=True).count() == 3

        group2.delete_in_progress(set_deleted_at=False)

        assert Run.all.count() == 3
        assert Run.all.filter(deleted_at__isnull=True).count() == 3

        group3 = RunFactory(project=self.project, kind=V1RunKind.DAG)
        run = RunFactory(
            project=self.project,
            pipeline=group3,
            status=V1Statuses.RUNNING,
            kind=V1RunKind.JOB,
        )

        assert Run.all.count() == 5
        assert Run.all.filter(deleted_at__isnull=True).count() == 5

        group3.delete_in_progress(set_deleted_at=False)

        assert Run.all.count() == 5
        assert Run.all.filter(deleted_at__isnull=True).count() == 5

        CronsDeletionManager.delete_in_progress_runs()

        assert Run.all.count() == 5
        assert (
            Run.all.filter(deleted_at__isnull=True).count() == 2
        )  # First run is pending

        run.status = V1Statuses.FAILED
        run.save()

        CronsDeletionManager.delete_in_progress_runs()

        assert Run.all.count() == 5
        assert Run.all.filter(deleted_at__isnull=True).count() == 0
