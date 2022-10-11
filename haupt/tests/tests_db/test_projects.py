#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.test import TestCase

from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.users import UserFactory
from haupt.db.managers.deleted import ArchivedManager, LiveManager
from haupt.db.models.projects import Project


class TestProjectModel(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()

    def test_managers(self):
        assert isinstance(Project.objects, LiveManager)
        assert isinstance(Project.archived, ArchivedManager)
