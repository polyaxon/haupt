#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.


from haupt import settings
from haupt.schemas.proxies_config import ProxiesConfig
from polyaxon.utils.test_utils import BaseTestCase


class BaseProxiesTestCase(BaseTestCase):
    SET_AUTH_SETTINGS = False
    SET_CLIENT_SETTINGS = False
    SET_CLI_SETTINGS = False
    SET_AGENT_SETTINGS = False

    def setUp(self):
        super().setUp()
        settings.PROXIES_CONFIG = ProxiesConfig()
