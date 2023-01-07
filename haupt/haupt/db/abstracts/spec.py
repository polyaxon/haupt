#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.db import models


class SpecModel(models.Model):
    raw_content = models.TextField(
        null=True,
        blank=True,
        help_text="The raw yaml content of the polyaxonfile/specification.",
    )
    content = models.TextField(
        null=True,
        blank=True,
        help_text="The compiled yaml content of the polyaxonfile/specification.",
    )

    class Meta:
        abstract = True
