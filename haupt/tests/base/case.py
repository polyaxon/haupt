from rest_framework import status

from haupt.common.test_cases.base import PolyaxonBaseTest, PolyaxonBaseTestSerializer
from haupt.common.test_clients.base import BaseClient
from haupt.db.defs import Models
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.factories.users import UserFactory
from haupt.db.models.projects import Project
from haupt.db.models.runs import Run
from polyaxon.utils.test_utils import patch_settings


class BaseTest(PolyaxonBaseTest):
    SET_AUTH_SETTINGS = True
    SET_CLIENT_SETTINGS = True
    SET_CLI_SETTINGS = True
    SET_AGENT_SETTINGS = False

    def setUp(self):
        super().setUp()
        patch_settings(
            set_auth=self.SET_AUTH_SETTINGS,
            set_client=self.SET_CLIENT_SETTINGS,
            set_cli=self.SET_CLI_SETTINGS,
            set_agent=self.SET_AGENT_SETTINGS,
        )

        self.client = BaseClient()
        self.user = UserFactory()


class BaseTestProjectSerializer(PolyaxonBaseTestSerializer):
    query = Project.all
    model_class = Project
    factory_class = ProjectFactory

    def create_one(self):
        return self.factory_class()


class BaseTestRunSerializer(PolyaxonBaseTestSerializer):
    query = Run.all
    model_class = Run
    factory_class = RunFactory

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()


class BaseTestBookmarkCreateView(BaseTest):
    model_class = None
    factory_class = None

    def get_url(self):
        raise NotImplementedError

    def create_object(self):
        raise NotImplementedError

    def setUp(self):
        super().setUp()
        self.object = self.create_object()
        self.url = self.get_url()

    def test_create(self):
        resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_201_CREATED
        assert Models.Bookmark.objects.count() == 1
        bookmark = Models.Bookmark.objects.first()
        assert bookmark.content_object == self.object


class BaseTestBookmarkDeleteView(BaseTest):
    model_class = None
    factory_class = None

    def get_url(self):
        raise NotImplementedError

    def create_object(self):
        raise NotImplementedError

    def setUp(self):
        super().setUp()
        self.object = self.create_object()
        self.url = self.get_url()

    def test_delete(self):
        resp = self.client.delete(self.url)
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        Models.Bookmark.objects.create(content_object=self.object)
        resp = self.client.delete(self.url)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert Models.Bookmark.objects.count() == 1
        bookmark = Models.Bookmark.objects.first()
        assert bookmark.content_object == self.object
        assert bookmark.enabled is False
