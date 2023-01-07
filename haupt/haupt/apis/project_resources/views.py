#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from django.conf import settings

from haupt.apis.endpoints.project import ProjectResourceListEndpoint
from haupt.apis.methods import project_resources as methods
from haupt.apis.serializers.artifacts import (
    RunArtifactLightSerializer,
    RunArtifactSerializer,
)
from haupt.apis.serializers.project_resources import (
    OfflineRunSerializer,
    OperationCreateSerializer,
    RunSerializer,
)
from haupt.common.apis.filters import OrderingFilter, QueryFilter
from haupt.common.apis.paginator import LargeLimitOffsetPagination
from haupt.common.endpoints.base import (
    CreateEndpoint,
    DestroyEndpoint,
    ListEndpoint,
    PostEndpoint,
)
from haupt.db.queries import artifacts as artifacts_queries
from haupt.db.queries import runs as runs_queries
from haupt.db.queries.artifacts import clean_sqlite_distinct_artifacts
from haupt.db.queries.runs import DEFAULT_COLUMNS_DEFER
from haupt.db.query_managers.artifact import ArtifactQueryManager
from haupt.db.query_managers.run import RunQueryManager


class ProjectRunsTagView(ProjectResourceListEndpoint, PostEndpoint):
    def post(self, request, *args, **kwargs):
        return methods.create_runs_tags(view=self, request=request, *args, **kwargs)


class ProjectRunsStopView(ProjectResourceListEndpoint, PostEndpoint):
    def post(self, request, *args, **kwargs):
        return methods.stop_runs(
            view=self, request=request, actor=self.project.actor, *args, **kwargs
        )


class ProjectRunsApproveView(ProjectResourceListEndpoint, PostEndpoint):
    def post(self, request, *args, **kwargs):
        return methods.approve_runs(
            view=self, request=request, actor=self.project.actor, *args, **kwargs
        )


class ProjectRunsDeleteView(ProjectResourceListEndpoint, DestroyEndpoint):
    def delete(self, request, *args, **kwargs):
        return methods.delete_runs(
            view=self, request=request, actor=self.project.actor, *args, **kwargs
        )


class ProjectRunsListView(ProjectResourceListEndpoint, ListEndpoint, CreateEndpoint):
    queryset = runs_queries.run_model.all.defer(*DEFAULT_COLUMNS_DEFER)
    filter_backends = (QueryFilter, OrderingFilter)
    query_manager = RunQueryManager
    check_alive = RunQueryManager.CHECK_ALIVE
    ordering = RunQueryManager.FIELDS_DEFAULT_ORDERING
    ordering_fields = RunQueryManager.FIELDS_ORDERING
    ordering_proxy_fields = RunQueryManager.FIELDS_ORDERING_PROXY
    serializer_class_mapping = {
        "GET": RunSerializer,
        "POST": OperationCreateSerializer,
    }

    def perform_create(self, serializer):
        serializer.save(project=self.project)


class ProjectRunsSyncView(ProjectResourceListEndpoint, CreateEndpoint):
    queryset = runs_queries.run_model.all.all()
    serializer_class = OfflineRunSerializer

    def perform_create(self, serializer):
        serializer.save(project=self.project)


class ProjectRunsArtifactsView(ProjectResourceListEndpoint, ListEndpoint):
    filter_backends = (QueryFilter, OrderingFilter)
    query_manager = ArtifactQueryManager
    check_alive = ArtifactQueryManager.CHECK_ALIVE
    ordering = ArtifactQueryManager.FIELDS_DEFAULT_ORDERING
    ordering_fields = ArtifactQueryManager.FIELDS_ORDERING
    ordering_proxy_fields = ArtifactQueryManager.FIELDS_ORDERING_PROXY
    pagination_class = LargeLimitOffsetPagination

    def enrich_queryset(self, queryset):
        return queryset.filter(run__project=self.project)

    def get_queryset(self):
        mode = self.request.query_params.get("mode")
        if not mode:
            return artifacts_queries.project_runs_artifacts
        return artifacts_queries.project_runs_artifacts_distinct

    def get_serializer_class(self):
        mode = self.request.query_params.get("mode")
        if not mode:
            return RunArtifactSerializer
        return RunArtifactLightSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        mode = self.request.query_params.get("mode")
        if settings.DB_ENGINE_NAME == "sqlite" and mode:
            (
                response.data["results"],
                response.data["count"],
            ) = clean_sqlite_distinct_artifacts(response.data["results"])
            return response
        return response
