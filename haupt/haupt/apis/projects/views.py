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
from haupt.db.defs import Models
from haupt.db.query_managers.project import ProjectQueryManager


class ProjectCreateView(BaseEndpoint, CreateAPIView):
    serializer_class = ProjectCreateSerializer


class ProjectListView(BaseEndpoint, ListEndpoint):
    queryset = Models.Project.all.only(
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
    queryset = Models.Project.objects.only("name").order_by("-updated_at")
    serializer_class = ProjectNameSerializer
    pagination_class = LargeLimitOffsetPagination


class ProjectDetailView(
    ProjectEndpoint, RetrieveEndpoint, UpdateEndpoint, DestroyEndpoint
):
    queryset = Models.Project.all
    serializer_class = ProjectDetailSerializer
