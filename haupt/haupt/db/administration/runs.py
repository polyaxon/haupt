#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.db.administration.utils import DiffModelAdmin, ReadOnlyAdmin


class RunLightAdmin(DiffModelAdmin, ReadOnlyAdmin):
    list_display = (
        "uuid",
        "user",
        "project",
        "name",
        "status",
        "created_at",
        "updated_at",
        "started_at",
        "finished_at",
    )
    fields = (
        "project",
        "name",
        "description",
        "status",
        "live_state",
        "created_at",
        "updated_at",
        "started_at",
        "finished_at",
    )
    readonly_fields = ("status",)
