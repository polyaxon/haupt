import tempfile

from django.conf import settings

from haupt.common.test_cases.base import PolyaxonBaseTest, PolyaxonBaseTestSerializer
from haupt.common.test_clients.base import BaseClient
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

        settings.ARTIFACTS_ROOT = tempfile.mkdtemp()
        settings.ARCHIVES_ROOT = tempfile.mkdtemp()
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
