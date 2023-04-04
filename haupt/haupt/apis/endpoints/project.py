#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from rest_framework.generics import get_object_or_404

from django.http import HttpRequest

from haupt.common.apis.regex import (
    NAME_KEY,
    OWNER_NAME_KEY,
    PROJECT_NAME_KEY,
    PROJECT_OWNER_NAME_KEY,
    UUID_KEY,
)
from haupt.common.endpoints.base import BaseEndpoint
from haupt.db.queries import projects as projects_queries


class ProjectEndpoint(BaseEndpoint):
    queryset = projects_queries.project_model.objects
    lookup_field = NAME_KEY
    lookup_url_kwarg = PROJECT_NAME_KEY
    CONTEXT_KEYS = (OWNER_NAME_KEY, PROJECT_NAME_KEY)
    CONTEXT_OBJECTS = ("project",)

    PROJECT_NAME_KEY = "name"
    PROJECT_OWNER_NAME_KEY = OWNER_NAME_KEY

    def initialize_object_context(self, request: HttpRequest, *args, **kwargs):
        #  pylint:disable=attribute-defined-outside-init
        self.project = self.get_object()

    def set_owner(self):
        self._owner_id = self.project.owner.id


class ProjectResourceListEndpoint(ProjectEndpoint):
    AUDITOR_EVENT_TYPES = None

    def get_object(self):
        if self._object:
            return self._object
        self._object = get_object_or_404(
            projects_queries.project_model,
            name=self.project_name,
        )
        return self._object

    def enrich_queryset(self, queryset):
        return queryset.filter(project=self.project)


class ProjectResourceEndpoint(ProjectEndpoint):
    AUDITOR_EVENT_TYPES = None
    lookup_field = UUID_KEY

    PROJECT_NAME_KEY = PROJECT_NAME_KEY
    PROJECT_OWNER_NAME_KEY = PROJECT_OWNER_NAME_KEY
