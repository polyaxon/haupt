#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from rest_framework.generics import CreateAPIView

from haupt.apis.endpoints.project import ProjectEndpoint
from haupt.apis.serializers.projects import (
    ProjectCreateSerializer,
    ProjectDetailSerializer,
    ProjectNameSerializer,
    ProjectSerializer,
)
from haupt.common.apis.filters import OrderingFilter, QueryFilter
from haupt.common.apis.paginator import LargeLimitOffsetPagination
from haupt.common.endpoints.base import (
    BaseEndpoint,
    DestroyEndpoint,
    ListEndpoint,
    RetrieveEndpoint,
    UpdateEndpoint,
)
from haupt.db.queries import projects as projects_queries
from haupt.db.query_managers.project import ProjectQueryManager


class ProjectCreateView(BaseEndpoint, CreateAPIView):
    serializer_class = ProjectCreateSerializer


class ProjectListView(BaseEndpoint, ListEndpoint):
    queryset = projects_queries.project_model.all.only(
        "uuid",
        "name",
        "description",
        "created_at",
        "updated_at",
        "tags",
    ).order_by("-updated_at")
    serializer_class = ProjectSerializer

    filter_backends = (QueryFilter, OrderingFilter)
    query_manager = ProjectQueryManager
    check_alive = ProjectQueryManager.CHECK_ALIVE
    ordering = ProjectQueryManager.FIELDS_DEFAULT_ORDERING
    ordering_fields = ProjectQueryManager.FIELDS_ORDERING
    ordering_proxy_fields = ProjectQueryManager.FIELDS_ORDERING_PROXY


class ProjectNameListView(BaseEndpoint, ListEndpoint):
    queryset = projects_queries.project_model.objects.only("name").order_by(
        "-updated_at"
    )
    serializer_class = ProjectNameSerializer
    pagination_class = LargeLimitOffsetPagination


class ProjectDetailView(
    ProjectEndpoint, RetrieveEndpoint, UpdateEndpoint, DestroyEndpoint
):
    queryset = projects_queries.project_model.all
    serializer_class = ProjectDetailSerializer
