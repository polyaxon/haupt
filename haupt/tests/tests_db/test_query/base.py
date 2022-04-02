#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.test import TestCase

from db.factories.projects import ProjectFactory
from db.factories.runs import RunFactory
from db.factories.users import UserFactory


class BaseTestQuery(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()
        self.run = RunFactory(project=self.project)
