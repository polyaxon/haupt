#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import tempfile

from django.conf import settings

from haupt.common.test_cases.base import PolyaxonBaseTest
from haupt.common.test_clients.base import BaseClient
from haupt.db.factories.users import UserFactory
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
        settings.LOGS_ROOT = tempfile.mkdtemp()
        settings.ARCHIVES_ROOT = tempfile.mkdtemp()
        self.client = BaseClient()
        self.user = UserFactory()
