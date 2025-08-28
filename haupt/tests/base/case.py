from rest_framework import status

from haupt.common.test_cases.base import PolyaxonBaseTest, PolyaxonBaseTestSerializer
from haupt.common.test_clients.base import BaseClient
from haupt.db.defs import Models
from haupt.db.factories.projects import ProjectFactory, ProjectVersionFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.factories.users import UserFactory
from haupt.db.models.project_stats import ProjectStats
from haupt.db.models.project_versions import ProjectVersion
from haupt.db.models.projects import Project
from haupt.db.models.runs import Run
from polyaxon._utils.test_utils import patch_settings
from polyaxon.schemas import V1ProjectVersionKind


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


class BaseTestProjectVersionSerializer(PolyaxonBaseTestSerializer):
    query = ProjectVersion.objects
    model_class = ProjectVersion
    factory_class = ProjectVersionFactory

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()

    def create_one(self):
        return self.factory_class(
            project=self.project, kind=V1ProjectVersionKind.COMPONENT
        )


class BaseTestProjectStatsSerializer(PolyaxonBaseTestSerializer):
    query = ProjectStats.objects
    model_class = ProjectStats

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()

    def create_one(self):
        stats = ProjectStats(
            project=self.project,
            user={"count": 1, "ids": [self.user.id]},
            run={"1": 1, "0": 2},
            status={"running": 1, "succeeded": 2},
            version={
                V1ProjectVersionKind.COMPONENT: 1,
                V1ProjectVersionKind.MODEL: 2,
                V1ProjectVersionKind.ARTIFACT: 3,
            },
            tracking_time={"1": 1111, "0": 200},
            wait_time={"1": 1111, "0": 200},
            resource_usage={
                "cpu": {"1": 1, "0": 2},
                "memory": {"1": 1, "0": 2},
                "gpu": {"1": 1, "0": 2},
            },
        )
        stats.save()
        return stats


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
