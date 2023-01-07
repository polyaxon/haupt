#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.db import models

from polyaxon import live_state


class LiveManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(live_state=live_state.STATE_LIVE)


class ArchivedManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(live_state=live_state.STATE_ARCHIVED)


class RestorableManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(
            live_state__in={live_state.STATE_LIVE, live_state.STATE_ARCHIVED}
        )
