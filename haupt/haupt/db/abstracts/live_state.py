#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import random

from django.db import models

from haupt.db.managers.deleted import ArchivedManager, LiveManager, RestorableManager
from polyaxon import live_state


class LiveStateModel(models.Model):
    live_state = models.IntegerField(
        null=True,
        blank=True,
        default=live_state.STATE_LIVE,
        choices=live_state.CHOICES,
        db_index=True,
    )

    objects = LiveManager()
    restorable = RestorableManager()
    all = models.Manager()
    archived = ArchivedManager()

    class Meta:
        abstract = True

    def delete_in_progress(self, update_name=False, commit=True) -> bool:
        if self.live_state == live_state.STATE_DELETION_PROGRESSING:
            return False

        if update_name:
            self.name = "del_{}_{}".format(
                self.name, getattr(self, "uuid", random.randint(-90, 100))
            )
        self.live_state = live_state.STATE_DELETION_PROGRESSING
        if commit:
            self.save(update_fields=["name", "live_state"])
        return True

    def archive(self, commit=True) -> bool:
        if (
            self.live_state == live_state.STATE_ARCHIVED
            or self.live_state == live_state.STATE_DELETION_PROGRESSING
        ):
            return False

        self.live_state = live_state.STATE_ARCHIVED
        if commit:
            self.save(update_fields=["live_state"])
        return True

    def restore(self) -> bool:
        if self.live_state != live_state.STATE_ARCHIVED:
            return False

        self.live_state = live_state.STATE_LIVE
        self.save(update_fields=["live_state"])
        return True
