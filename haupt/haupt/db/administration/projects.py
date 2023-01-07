#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.db.administration.utils import DiffModelAdmin


class ProjectAdmin(DiffModelAdmin):
    list_display = ("uuid", "name", "created_at", "updated_at")
    list_display_links = ("uuid", "name")
    readonly_fields = DiffModelAdmin.readonly_fields + ("name",)
    fields = ("name", "live_state", "created_at", "updated_at")

    def get_queryset(self, request):
        qs = self.model.all.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
