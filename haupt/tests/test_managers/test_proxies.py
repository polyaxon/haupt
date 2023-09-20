import pytest

from haupt.managers.proxies import ProxiesManager
from haupt.schemas.proxies_config import ProxiesConfig
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestProxiesConfigManager(BaseTestCase):
    def test_default_props(self):
        assert ProxiesManager.is_global() is True
        assert ProxiesManager.is_all_visibility() is False
        assert ProxiesManager.CONFIG_PATH is None
        assert ProxiesManager.IN_PROJECT_DIR is False
        assert ProxiesManager.CONFIG_FILE_NAME == ".proxies"
        assert ProxiesManager.CONFIG == ProxiesConfig
