from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from django.conf import settings

from haupt.apis.bookmarks.views import BookmarkCreateView, BookmarkDeleteView
from haupt.apis.endpoints.project import ProjectEndpoint
from haupt.apis.serializers.base.bookmarks_mixin import BookmarkedListMixinView
from haupt.apis.serializers.project_stats import ProjectStatsSerializer
from haupt.apis.serializers.projects import (
    BookmarkedProjectSerializer,
    ProjectCreateSerializer,
    ProjectDetailSerializer,
    ProjectNameSerializer,
)
from haupt.common.apis.filters import OrderingFilter, QueryFilter
from haupt.common.apis.paginator import LargeLimitOffsetPagination
from haupt.common.content_types import ContentTypes
from haupt.common.endpoints.base import (
    BaseEndpoint,
    DestroyEndpoint,
    ListEndpoint,
    PostEndpoint,
    RetrieveEndpoint,
    UpdateEndpoint,
)
from haupt.common.endpoints.mixins import StatsMixin
from haupt.common.events.registry.archive import (
    PROJECT_ARCHIVED_ACTOR,
    PROJECT_RESTORED_ACTOR,
)
from haupt.common.events.registry.bookmark import (
    PROJECT_BOOKMARKED_ACTOR,
    PROJECT_UNBOOKMARKED_ACTOR,
)
from haupt.common.events.registry.project import PROJECT_STATS_ACTOR
from haupt.db.defs import Models
from haupt.db.managers.live_state import (
    archive_project,
    delete_in_progress_project,
    restore_project,
)
from haupt.db.managers.projects import add_project_contributors
from haupt.db.managers.stats import StatsSerializer
from haupt.db.query_managers.project import ProjectQueryManager
from polyaxon._services.values import PolyaxonServices


class ProjectCreateView(BaseEndpoint, CreateAPIView):
    serializer_class = ProjectCreateSerializer
    ALLOWED_METHODS = ["POST"]


ADDITIONAL_ONLY_FIELD = ["is_public"] if settings.HAS_ORG_MANAGEMENT else []


class ProjectsListMixinView(BookmarkedListMixinView):
    queryset = Models.Project.all.only(
        "uuid",
        "name",
        "description",
        "created_at",
        "updated_at",
        "tags",
        "live_state",
        *ADDITIONAL_ONLY_FIELD,
    ).order_by("-updated_at")
    serializer_class = BookmarkedProjectSerializer

    bookmarked_model = "project"
    query_manager = ProjectQueryManager
    check_alive = ProjectQueryManager.CHECK_ALIVE
    ordering = ProjectQueryManager.FIELDS_DEFAULT_ORDERING
    ordering_fields = ProjectQueryManager.FIELDS_ORDERING
    ordering_proxy_fields = ProjectQueryManager.FIELDS_ORDERING_PROXY

    ALLOWED_METHODS = ["GET"]


class ProjectListView(ProjectsListMixinView, BaseEndpoint, ListEndpoint):
    pass


class ProjectNameListMixin:
    queryset = Models.Project.objects.only("name").order_by("-updated_at")
    serializer_class = ProjectNameSerializer
    pagination_class = LargeLimitOffsetPagination
    filter_backends = (QueryFilter, OrderingFilter)
    query_manager = ProjectQueryManager
    check_alive = ProjectQueryManager.CHECK_ALIVE
    ordering = ProjectQueryManager.FIELDS_DEFAULT_ORDERING
    ordering_fields = ProjectQueryManager.FIELDS_ORDERING
    ordering_proxy_fields = ProjectQueryManager.FIELDS_ORDERING_PROXY
    ALLOWED_METHODS = ["GET"]


class ProjectNameListView(ProjectNameListMixin, BaseEndpoint, ListEndpoint):
    pass


class ProjectDetailView(
    ProjectEndpoint, RetrieveEndpoint, UpdateEndpoint, DestroyEndpoint
):
    queryset = (
        Models.Project.all.select_related("owner").prefetch_related("contributors")
        if settings.HAS_ORG_MANAGEMENT
        else Models.Project.all
    )
    serializer_class = ProjectDetailSerializer
    ALLOWED_METHODS = ["GET", "PUT", "PATCH", "DELETE"]
    AUDIT_OWNER = True
    AUDIT_PROJECT = True
    AUDIT_INSTANCE = True

    def perform_update(self, serializer):
        instance = serializer.save()
        add_project_contributors(instance, users=[self.request.user])

    def perform_destroy(self, instance):
        delete_in_progress_project(instance)


class ProjectArchiveView(ProjectEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]
    AUDITOR_EVENT_TYPES = {"POST": PROJECT_ARCHIVED_ACTOR}
    AUDIT_PROJECT = True
    AUDIT_OWNER = True
    AUDIT_INSTANCE = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        add_project_contributors(obj, users=[self.request.user])
        archive_project(obj)
        self.audit(request, *args, **kwargs)
        return Response(status=status.HTTP_200_OK, data={})


class ProjectRestoreView(ProjectEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]
    AUDITOR_EVENT_TYPES = {"POST": PROJECT_RESTORED_ACTOR}
    AUDIT_PROJECT = True
    AUDIT_OWNER = True
    AUDIT_INSTANCE = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        add_project_contributors(obj, users=[self.request.user])
        self.audit(request, *args, **kwargs)
        restore_project(obj)
        return Response(status=status.HTTP_200_OK, data={})


class ProjectBookmarkCreateView(ProjectEndpoint, BookmarkCreateView):
    content_type = ContentTypes.PROJECT.value
    ALLOWED_METHODS = ["POST"]
    AUDITOR_EVENT_TYPES = {"POST": PROJECT_BOOKMARKED_ACTOR}
    AUDIT_PROJECT = True
    AUDIT_OWNER = True
    AUDIT_INSTANCE = True


class ProjectBookmarkDeleteView(ProjectEndpoint, BookmarkDeleteView):
    content_type = ContentTypes.PROJECT.value
    ALLOWED_METHODS = ["DELETE"]
    AUDITOR_EVENT_TYPES = {"DELETE": PROJECT_UNBOOKMARKED_ACTOR}
    AUDIT_PROJECT = True
    AUDIT_OWNER = True
    AUDIT_INSTANCE = True


class ProjectStatsView(ProjectEndpoint, RetrieveEndpoint, StatsMixin):
    queryset = (
        Models.Project.all.select_related("owner")
        if settings.HAS_ORG_MANAGEMENT
        else Models.Project.all
    )
    AUDITOR_EVENT_TYPES = {
        "GET": PROJECT_STATS_ACTOR,
    }
    ALLOWED_SERVICES = [PolyaxonServices.UI]
    CHECK_SERVICE = True
    ALLOWED_METHODS = ["GET"]
    AUDIT_OWNER = True
    AUDIT_PROJECT = True
    AUDIT_INSTANCE = True
    bookmarked_model = "run"

    def get_queryset(self):
        mode = self.validate_stats_mode()
        queryset = super().get_queryset()
        if mode == "stats":
            return queryset.select_related("latest_stats")
        return queryset

    def get_serializer(self, *args, **kwargs):
        mode = self.validate_stats_mode()
        if mode == "stats":
            return ProjectStatsSerializer(self.project.latest_stats)
        queryset = Models.Run.objects.filter(project_id=self.project.id)
        queryset = StatsSerializer.filter_queryset(
            queryset=queryset,
            request=self.request,
            view=self,
        )
        return StatsSerializer(
            queryset=queryset,
            kind=self.request.query_params.get("kind"),
            aggregate=self.request.query_params.get("aggregate"),
            groupby=self.request.query_params.get("groupby"),
            trunc=self.request.query_params.get("trunc"),
        )
