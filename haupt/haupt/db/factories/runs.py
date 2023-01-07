#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import factory

from haupt.db.abstracts.getter import get_run_model
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.users import UserFactory


class RunFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
    original = None
    pipeline = None
    is_managed = False

    class Meta:
        model = get_run_model()
