#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.apis.endpoints.run import RunArtifactEndpoint, RunResourceListEndpoint
from haupt.apis.methods import run_lineage as methods
from haupt.apis.serializers.artifacts import (
    RunArtifactNameSerializer,
    RunArtifactSerializer,
)
from haupt.common.apis.filters import OrderingFilter, QueryFilter
from haupt.common.apis.paginator import LargeLimitOffsetPagination
from haupt.common.apis.regex import RUN_UUID_KEY
from haupt.common.endpoints.base import (
    CreateEndpoint,
    DestroyEndpoint,
    ListEndpoint,
    RetrieveEndpoint,
)
from haupt.common.events.registry.run import RUN_NEW_ARTIFACTS
from haupt.db.queries import artifacts as artifacts_queries
from haupt.db.query_managers.artifact import ArtifactQueryManager


class RunArtifactListView(RunResourceListEndpoint, ListEndpoint, CreateEndpoint):
    queryset = artifacts_queries.artifacts
    serializer_class = RunArtifactSerializer
    pagination_class = LargeLimitOffsetPagination
    AUDITOR_EVENT_TYPES = {
        "POST": RUN_NEW_ARTIFACTS,
    }
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_EXTRA_KEYS = ("artifacts",)
    AUDIT_INSTANCE = True

    filter_backends = (QueryFilter, OrderingFilter)
    query_manager = ArtifactQueryManager
    check_alive = ArtifactQueryManager.CHECK_ALIVE
    ordering = ArtifactQueryManager.FIELDS_DEFAULT_ORDERING
    ordering_fields = ArtifactQueryManager.FIELDS_ORDERING
    ordering_proxy_fields = ArtifactQueryManager.FIELDS_ORDERING_PROXY

    def create(self, request, *args, **kwargs):
        return methods.create(view=self, request=request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["run"] = self.run
        return context


class RunArtifactNameListView(RunResourceListEndpoint, ListEndpoint):
    queryset = artifacts_queries.artifacts_names
    serializer_class = RunArtifactNameSerializer
    pagination_class = LargeLimitOffsetPagination


class RunArtifactDetailView(RunArtifactEndpoint, RetrieveEndpoint, DestroyEndpoint):
    queryset = artifacts_queries.artifacts
    serializer_class = RunArtifactSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["run"] = self.run_artifact.run
        return context
