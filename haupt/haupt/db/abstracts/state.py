#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.db import models


class StateModel(models.Model):
    state = models.UUIDField(db_index=True)

    class Meta:
        abstract = True


class OptionalStateModel(models.Model):
    state = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True
