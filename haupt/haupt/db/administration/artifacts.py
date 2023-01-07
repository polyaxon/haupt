#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.db.administration.utils import DiffModelAdmin


class ArtifactAdmin(DiffModelAdmin):
    list_display = (
        "name",
        "kind",
        "state",
    )
    list_display_links = (
        "name",
        "kind",
        "state",
    )
    readonly_fields = DiffModelAdmin.readonly_fields + ("name",)
    fields = ("name", "kind", "created_at", "updated_at")
