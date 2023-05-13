from haupt.common.test_cases.base import PolyaxonBaseTest
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.users import UserFactory


class BaseTest(PolyaxonBaseTest):
    def setUp(self):
        super().setUp()
        # Force tasks autodiscover
        from haupt.background.scheduler import tasks  # noqa

        self.user = UserFactory()
        self.project = ProjectFactory()
