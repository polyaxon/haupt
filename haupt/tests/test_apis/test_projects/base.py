#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.factories.users import UserFactory
from haupt.db.models.projects import Project
from polyaxon.api import API_V1
from tests.base.case import BaseTest


class BaseTestProjectApi(BaseTest):
    model_class = Project
    factory_class = ProjectFactory

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = self.factory_class()
        self.url = "/{}/{}/{}/".format(API_V1, self.user.username, self.project.name)
        self.queryset = self.model_class.objects.filter()
        self.object_query = self.model_class.objects.get(id=self.project.id)

        # Create related fields
        for _ in range(2):
            RunFactory(user=self.user, project=self.project)
