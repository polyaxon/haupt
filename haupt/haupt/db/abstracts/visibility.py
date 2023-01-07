#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.db import models


class VisibilityModel(models.Model):
    is_public = models.BooleanField(
        default=False, help_text="If the entity is public or private."
    )

    class Meta:
        abstract = True
