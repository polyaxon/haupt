import pytest

from haupt.managers.sandbox import SandboxConfigManager
from haupt.schemas.sandbox_config import SandboxConfig
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestSandboxConfigManager(BaseTestCase):
    def test_default_props(self):
        assert SandboxConfigManager.is_global() is False
        assert SandboxConfigManager.is_all_visibility() is True
        assert SandboxConfigManager.CONFIG_PATH is None
        assert SandboxConfigManager.IN_PROJECT_DIR is False
        assert SandboxConfigManager.CONFIG_FILE_NAME == ".sandbox"
        assert SandboxConfigManager.CONFIG == SandboxConfig
