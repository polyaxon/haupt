#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from polyaxon.lifecycle import V1Statuses
from polyaxon.utils.enums_utils import values_to_choices


class StatusModel(models.Model):
    status = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        db_index=True,
        default=V1Statuses.CREATED,
        choices=values_to_choices(V1Statuses.allowable_values),
    )
    status_conditions = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )

    class Meta:
        abstract = True
