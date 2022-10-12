#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import pytest

from haupt.managers.sandbox import SandboxConfigManager
from haupt.schemas.sandbox_config import SandboxConfig
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestSandboxConfigManager(BaseTestCase):
    def test_default_props(self):
        assert SandboxConfigManager.is_global() is False
        assert SandboxConfigManager.is_all_visibility() is True
        assert SandboxConfigManager.CONFIG_PATH is None
        assert SandboxConfigManager.IS_POLYAXON_DIR is False
        assert SandboxConfigManager.CONFIG_FILE_NAME == ".sandbox"
        assert SandboxConfigManager.CONFIG == SandboxConfig
