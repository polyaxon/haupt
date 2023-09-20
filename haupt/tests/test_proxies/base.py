from haupt import settings
from haupt.schemas.proxies_config import ProxiesConfig
from polyaxon._utils.test_utils import BaseTestCase


class BaseProxiesTestCase(BaseTestCase):
    SET_AUTH_SETTINGS = False
    SET_CLIENT_SETTINGS = False
    SET_CLI_SETTINGS = False
    SET_AGENT_SETTINGS = False

    def setUp(self):
        super().setUp()
        settings.PROXIES_CONFIG = ProxiesConfig()
