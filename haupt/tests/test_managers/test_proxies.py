#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import pytest

from haupt.managers.proxies import ProxiesManager
from haupt.schemas.proxies_config import ProxiesConfig
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestProxiesConfigManager(BaseTestCase):
    def test_default_props(self):
        assert ProxiesManager.is_global() is True
        assert ProxiesManager.is_all_visibility() is False
        assert ProxiesManager.CONFIG_PATH is None
        assert ProxiesManager.IS_POLYAXON_DIR is False
        assert ProxiesManager.CONFIG_FILE_NAME == ".proxies"
        assert ProxiesManager.CONFIG == ProxiesConfig
