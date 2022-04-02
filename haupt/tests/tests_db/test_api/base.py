#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from common.test_cases.base import PolyaxonBaseTestSerializer
from db.factories.projects import ProjectFactory
from db.factories.runs import RunFactory
from db.factories.users import UserFactory
from db.models.projects import Project
from db.models.runs import Run


class BaseTestProjectSerializer(PolyaxonBaseTestSerializer):
    query = Project.all
    model_class = Project
    factory_class = ProjectFactory

    def create_one(self):
        return self.factory_class()


class BaseTestRunSerializer(PolyaxonBaseTestSerializer):
    query = Run.all
    model_class = Run
    factory_class = RunFactory

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()
