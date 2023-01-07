#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import uuid

from django.db import models


class UuidModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=False)

    class Meta:
        abstract = True
