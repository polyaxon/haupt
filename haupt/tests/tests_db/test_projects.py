#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.test import TestCase

from db.factories.projects import ProjectFactory
from db.factories.users import UserFactory
from db.managers.deleted import ArchivedManager, LiveManager
from db.models.projects import Project


class TestProjectModel(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()

    def test_managers(self):
        assert isinstance(Project.objects, LiveManager)
        assert isinstance(Project.archived, ArchivedManager)
