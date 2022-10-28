#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

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
