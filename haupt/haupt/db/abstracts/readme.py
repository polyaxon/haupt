#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.db import models


class ReadmeModel(models.Model):
    readme = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    @property
    def has_readme(self) -> bool:
        return bool(self.readme)
