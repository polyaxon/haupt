#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404

from haupt.apis.endpoints.project import ProjectResourceEndpoint
from haupt.common.apis.regex import (
    ARTIFACT_NAME_KEY,
    NAME_KEY,
    OWNER_NAME_KEY,
    PROJECT_NAME_KEY,
    RUN_UUID_KEY,
    UUID_KEY,
)
from haupt.db.queries import artifacts as artifacts_queries
from haupt.db.queries import runs as runs_queries


class RunEndpoint(ProjectResourceEndpoint):
    queryset = runs_queries.run_model.all.select_related("project")
    lookup_field = UUID_KEY
    lookup_url_kwarg = RUN_UUID_KEY
    CONTEXT_KEYS = (OWNER_NAME_KEY, PROJECT_NAME_KEY, RUN_UUID_KEY)
    CONTEXT_OBJECTS = ("run",)

    def enrich_queryset(self, queryset):
        return queryset.filter(project__name=self.project_name)

    def set_owner(self):
        self.project = self.run.project
        self._owner_id = self.project.owner_id

    def initialize_object_context(self, request: HttpRequest, *args, **kwargs):
        #  pylint:disable=attribute-defined-outside-init
        self.run = self.get_object()


class RunResourceListEndpoint(RunEndpoint):
    AUDITOR_EVENT_TYPES = None

    def get_object(self):
        if self._object:
            return self._object

        self._object = get_object_or_404(
            runs_queries.run_model.all.select_related("project"),
            uuid=self.run_uuid,
            project__name=self.project_name,
        )

        # May raise a permission denied
        self.check_object_permissions(self.request, self._object)

        return self._object

    def enrich_queryset(self, queryset):
        return queryset.filter(run=self.run)


class RunArtifactEndpoint(RunEndpoint):
    AUDITOR_EVENT_TYPES = None
    lookup_field = NAME_KEY
    lookup_url_kwarg = ARTIFACT_NAME_KEY
    CONTEXT_KEYS = (PROJECT_NAME_KEY, RUN_UUID_KEY, ARTIFACT_NAME_KEY)
    CONTEXT_OBJECTS = ("run_artifact",)

    def enrich_queryset(self, queryset):
        return queryset.filter(
            run__uuid=self.run_uuid,
            run__project__name=self.project_name,
        )

    def set_owner(self):
        self.project = self.run_artifact.run.project
        self._owner_id = self.project.owner_id

    def initialize_object_context(self, request: HttpRequest, *args, **kwargs):
        #  pylint:disable=attribute-defined-outside-init
        self.run_artifact = self.get_object()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            return queryset.get(artifact__name=self.artifact_name)
        except artifacts_queries.lineage_model.DoesNotExist:
            raise Http404(
                "No %s matches the given query." % self.queryset.model._meta.object_name
            )
