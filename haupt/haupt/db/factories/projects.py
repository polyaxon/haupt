#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import factory

from haupt.db.abstracts.getter import get_project_model


class ProjectFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence("project-{}".format)

    class Meta:
        model = get_project_model()
