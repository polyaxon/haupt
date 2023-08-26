from django.test import TestCase

from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.managers.live_state import (
    archive_project,
    archive_run,
    confirm_delete_run,
    delete_in_progress_project,
    delete_in_progress_run,
    restore_project,
    restore_run,
)
from haupt.db.models.runs import Run
from polyaxon.lifecycle import LiveState, ManagedBy, V1Statuses


class TestArchiveRestoreDelete(TestCase):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()
        self.run = RunFactory(
            project=self.project,
            managed_by=ManagedBy.USER,
        )

    def test_project_archive_deletion_in_progres_restore(self):
        assert self.project.live_state == LiveState.LIVE
        assert self.project.archived_at is None
        assert self.project.deleted_at is None
        assert self.project.runs.count() == 1
        assert Run.all.filter(project=self.project).count() == 1
        last_run = Run.all.last()
        assert last_run.archived_at is None
        assert last_run.deleted_at is None

        archive_project(self.project)
        assert self.project.live_state == LiveState.ARCHIVED
        assert self.project.archived_at is not None
        assert self.project.deleted_at is None
        assert self.project.runs.count() == 0
        assert Run.all.filter(project=self.project).count() == 1
        last_run = Run.all.last()
        assert last_run.archived_at is not None
        assert last_run.deleted_at is None

        restore_project(self.project)
        assert self.project.live_state == LiveState.LIVE
        assert self.project.archived_at is None
        assert self.project.deleted_at is None
        assert self.project.runs.count() == 1
        assert Run.all.filter(project=self.project).count() == 1
        last_run = Run.all.last()
        assert last_run.archived_at is None
        assert last_run.deleted_at is None

        delete_in_progress_project(self.project)
        assert self.project.archived_at is None
        assert self.project.deleted_at is not None
        assert self.project.live_state == LiveState.DELETION_PROGRESSING
        assert self.project.runs.count() == 0
        assert Run.all.filter(project=self.project).count() == 1
        last_run = Run.all.last()
        assert last_run.archived_at is None
        assert last_run.deleted_at is None

        # Cannot archive deletion in progress
        archive_project(self.project)
        assert self.project.archived_at is None
        assert self.project.deleted_at is not None
        assert self.project.live_state == LiveState.DELETION_PROGRESSING
        assert self.project.runs.count() == 0
        assert Run.all.filter(project=self.project).count() == 1
        last_run = Run.all.last()
        assert last_run.archived_at is None
        assert last_run.deleted_at is None

        # Manually restore
        self.project.live_state = LiveState.LIVE
        self.project.runs.update(live_state=LiveState.ARCHIVED)

        delete_in_progress_project(self.project)
        assert self.project.archived_at is None
        assert self.project.deleted_at is not None
        assert self.project.live_state == LiveState.DELETION_PROGRESSING
        assert self.project.runs.count() == 0
        assert Run.all.filter(project=self.project).count() == 1

        # Cannot restore deletion in progress
        restore_project(self.project)
        assert self.project.archived_at is None
        assert self.project.deleted_at is not None
        assert self.project.live_state == LiveState.DELETION_PROGRESSING
        assert self.project.runs.count() == 0
        assert Run.all.filter(project=self.project).count() == 1
        last_run = Run.all.last()
        assert last_run.archived_at is None
        assert last_run.deleted_at is None

    def test_archive_trigger_stopping(self):
        assert self.project.live_state == LiveState.LIVE
        assert self.project.runs.count() == 1
        last_run = Run.all.last()
        assert last_run.archived_at is None
        assert last_run.deleted_at is None
        assert Run.all.filter(project=self.project).count() == 1
        assert set(
            Run.all.filter(project=self.project).values_list("status", flat=True)
        ) != {V1Statuses.STOPPING}

        archive_project(self.project)
        assert self.project.live_state == LiveState.ARCHIVED
        assert self.project.runs.count() == 0
        assert Run.all.filter(project=self.project).count() == 1
        assert set(
            Run.all.filter(project=self.project).values_list("status", flat=True)
        ) == {V1Statuses.STOPPING}
        last_run = Run.all.last()
        assert last_run.archived_at is not None
        assert last_run.deleted_at is None

    def test_run_archive_restore(self):
        assert self.run.live_state == LiveState.LIVE
        assert Run.objects.count() == 1
        assert Run.all.count() == 1
        last_run = Run.all.last()
        assert last_run.status != V1Statuses.STOPPING
        assert last_run.archived_at is None
        assert last_run.deleted_at is None

        archive_run(self.run)
        assert self.run.live_state == LiveState.ARCHIVED
        assert Run.objects.count() == 0
        assert Run.all.count() == 1
        last_run = Run.all.last()
        assert last_run.status == V1Statuses.STOPPING
        assert last_run.archived_at is not None
        assert last_run.deleted_at is None

        restore_run(self.run)
        assert self.run.live_state == LiveState.LIVE
        assert Run.objects.count() == 1
        assert Run.all.count() == 1
        last_run = Run.all.last()
        assert last_run.status == V1Statuses.STOPPING
        assert last_run.archived_at is None
        assert last_run.deleted_at is None

        delete_in_progress_run(self.run)
        assert self.run.live_state == LiveState.DELETION_PROGRESSING
        assert Run.objects.count() == 0
        assert Run.all.count() == 1
        last_run = Run.all.last()
        assert last_run.status == V1Statuses.STOPPING
        assert last_run.archived_at is None
        assert last_run.deleted_at is None

        # Cannot archive deletion in progress
        archive_run(self.run)
        assert self.run.live_state == LiveState.DELETION_PROGRESSING
        assert Run.objects.count() == 0
        assert Run.all.count() == 1
        last_run = Run.all.last()
        assert last_run.status == V1Statuses.STOPPING
        assert last_run.archived_at is None
        assert last_run.deleted_at is None

        # Manually set to live
        self.run.live_state = LiveState.LIVE
        self.run.save()

        delete_in_progress_run(self.run)
        assert self.run.live_state == LiveState.DELETION_PROGRESSING
        assert Run.objects.count() == 0
        assert Run.all.count() == 1
        last_run = Run.all.last()
        assert last_run.status == V1Statuses.STOPPING
        assert last_run.archived_at is None
        assert last_run.deleted_at is None

        # Cannot restore deletion in progress
        restore_run(self.run)
        assert self.run.live_state == LiveState.DELETION_PROGRESSING
        assert Run.objects.count() == 0
        assert Run.all.count() == 1
        last_run = Run.all.last()
        assert last_run.status == V1Statuses.STOPPING
        assert last_run.archived_at is None
        assert last_run.deleted_at is None

        confirm_delete_run(self.run)
        assert self.run.live_state == LiveState.DELETION_PROGRESSING
        assert Run.objects.count() == 0
        assert Run.all.count() == 1
        last_run = Run.all.last()
        assert last_run.status == V1Statuses.STOPPING
        assert last_run.archived_at is None
        assert last_run.deleted_at is not None

        restore_run(self.run)
        assert self.run.live_state == LiveState.DELETION_PROGRESSING
        assert Run.objects.count() == 0
        assert Run.all.count() == 1
        last_run = Run.all.last()
        assert last_run.status == V1Statuses.STOPPING
        assert last_run.archived_at is None
        assert last_run.deleted_at is not None

        # Cannot archive deleted
        archive_run(self.run)
        assert self.run.live_state == LiveState.DELETION_PROGRESSING
        assert Run.objects.count() == 0
        assert Run.all.count() == 1
        last_run = Run.all.last()
        assert last_run.status == V1Statuses.STOPPING
        assert last_run.archived_at is None
        assert last_run.deleted_at is not None

        # Manually set to live
        self.run.live_state = LiveState.LIVE
        self.run.save()

        archive_run(self.run)
        assert self.run.live_state == LiveState.ARCHIVED
        assert Run.objects.count() == 0
        assert Run.all.count() == 1
        last_run = Run.all.last()
        assert last_run.status == V1Statuses.STOPPING
        assert last_run.archived_at is not None
        assert last_run.deleted_at is not None

        # Cannot restore deletion in progress
        confirm_delete_run(self.run)
        assert self.run.live_state == LiveState.ARCHIVED
        assert Run.objects.count() == 0
        assert Run.all.count() == 1
        last_run = Run.all.last()
        assert last_run.status == V1Statuses.STOPPING
        assert last_run.archived_at is not None
        assert last_run.deleted_at is not None
