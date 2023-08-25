from django.test import TestCase

from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.models.bookmarks import Bookmark


class TestBookmarkModel(TestCase):
    def _create_bookmark(self, obj):
        return Bookmark.objects.create(content_object=obj)

    def test_bookmark_project(self):
        assert Bookmark.objects.count() == 0
        project = ProjectFactory()
        bookmark = self._create_bookmark(project)
        assert bookmark.content_object == project
        assert Bookmark.objects.count() == 1
        # Delete project results in deleting the bookmark
        project.delete()
        assert Bookmark.objects.count() == 0

    def test_bookmark_run(self):
        assert Bookmark.objects.count() == 0
        project = ProjectFactory()
        run = RunFactory(project=project)
        bookmark = self._create_bookmark(run)
        assert bookmark.content_object == run
        assert Bookmark.objects.count() == 1
        # Delete run results in deleting the bookmark
        run.delete()
        assert Bookmark.objects.count() == 0
