from django.conf import settings

from haupt.apis.endpoints.project import ProjectResourceListEndpoint
from haupt.apis.methods import project_resources as methods
from haupt.apis.serializers.artifacts import (
    RunArtifactLightSerializer,
    RunArtifactSerializer,
)
from haupt.apis.serializers.base.bookmarks_mixin import BookmarkedListMixinView
from haupt.apis.serializers.runs import (
    BookmarkedRunSerializer,
    BookmarkedTimelineRunSerializer,
    GraphRunSerializer,
    OfflineRunSerializer,
    OperationCreateSerializer,
)
from haupt.common.apis.filters import OrderingFilter, QueryFilter
from haupt.common.apis.paginator import LargeLimitOffsetPagination
from haupt.common.endpoints.base import (
    CreateEndpoint,
    DestroyEndpoint,
    ListEndpoint,
    PostEndpoint,
)
from haupt.db.defs import Models
from haupt.db.managers.flows import get_run_graph
from haupt.db.queries import artifacts as artifacts_queries
from haupt.db.queries.artifacts import clean_sqlite_distinct_artifacts
from haupt.db.queries.runs import DEFAULT_COLUMNS_DEFER
from haupt.db.query_managers.artifact import ArtifactQueryManager
from haupt.db.query_managers.run import RunQueryManager


class ProjectRunsTagView(ProjectResourceListEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]

    def post(self, request, *args, **kwargs):
        return methods.create_runs_tags(view=self, request=request, *args, **kwargs)


class ProjectRunsStopView(ProjectResourceListEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]

    def post(self, request, *args, **kwargs):
        return methods.stop_runs(
            view=self, request=request, actor=request.user, *args, **kwargs
        )


class ProjectRunsSkipView(ProjectResourceListEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]

    def post(self, request, *args, **kwargs):
        return methods.skip_runs(
            view=self, request=request, actor=request.user, *args, **kwargs
        )


class ProjectRunsApproveView(ProjectResourceListEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]

    def post(self, request, *args, **kwargs):
        return methods.approve_runs(
            view=self, request=request, actor=request.user, *args, **kwargs
        )


class ProjectRunsInvalidateView(ProjectResourceListEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]

    def post(self, request, *args, **kwargs):
        return methods.invalidate_runs(
            view=self, request=request, actor=self.request.user, *args, **kwargs
        )


class ProjectRunsBookmarkView(ProjectResourceListEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]

    def post(self, request, *args, **kwargs):
        return methods.bookmarks_runs(
            view=self, request=request, actor=self.request.user, *args, **kwargs
        )


class ProjectRunsArchiveView(ProjectResourceListEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]

    def post(self, request, *args, **kwargs):
        return methods.archive_runs(
            view=self, request=request, actor=request.user, *args, **kwargs
        )


class ProjectRunsRestoreView(ProjectResourceListEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]

    def post(self, request, *args, **kwargs):
        return methods.restore_runs(
            view=self, request=request, actor=request.user, *args, **kwargs
        )


class ProjectRunsTransferView(ProjectResourceListEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]

    def post(self, request, *args, **kwargs):
        return methods.transfer_runs(
            view=self, request=request, actor=request.user, *args, **kwargs
        )


class ProjectRunsDeleteView(ProjectResourceListEndpoint, DestroyEndpoint):
    ALLOWED_METHODS = ["DELETE"]

    def _pre_delete_check(self, request):
        pass

    def delete(self, request, *args, **kwargs):
        self._pre_delete_check(request)
        return methods.delete_runs(
            view=self, request=request, actor=self.request.user, *args, **kwargs
        )


class ProjectRunsListMixinView(BookmarkedListMixinView):
    bookmarked_model = "run"

    def handle_graph(self, serializer_class, *args, **kwargs):
        queryset = args[0]

        if not queryset:
            return super().get_serializer(*args, **kwargs)

        object_ids = {o.id for o in queryset}

        # Get graph
        graph = get_run_graph({"id__in": object_ids})

        context = self.get_serializer_context()
        context["graph"] = graph
        kwargs["context"] = context
        return serializer_class(*args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        if serializer_class == GraphRunSerializer:
            return self.handle_graph(serializer_class, *args, **kwargs)

        return super().get_serializer(*args, **kwargs)


class ProjectRunsListView(
    ProjectRunsListMixinView, ProjectResourceListEndpoint, ListEndpoint, CreateEndpoint
):
    queryset = Models.Run.all.prefetch_related("original", "pipeline", "user").defer(
        *DEFAULT_COLUMNS_DEFER
    )
    pagination_class = LargeLimitOffsetPagination
    query_manager = RunQueryManager
    check_alive = RunQueryManager.CHECK_ALIVE
    ordering = RunQueryManager.FIELDS_DEFAULT_ORDERING
    ordering_fields = RunQueryManager.FIELDS_ORDERING
    ordering_proxy_fields = RunQueryManager.FIELDS_ORDERING_PROXY
    AUDIT_OWNER = True
    AUDIT_PROJECT = True
    AUDIT_INSTANCE = True
    ALLOWED_METHODS = ["GET", "POST"]
    serializer_class_mapping = {
        "GET": BookmarkedRunSerializer,
        "POST": OperationCreateSerializer,
    }

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OperationCreateSerializer
        elif self.request.method == "GET":
            if self.request.query_params.get("mode") == "timeline":
                return BookmarkedTimelineRunSerializer
            elif self.request.query_params.get("mode") == "graph":
                return GraphRunSerializer
            else:
                return BookmarkedRunSerializer

        else:
            return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(project=self.project)


class ProjectRunsSyncView(ProjectResourceListEndpoint, CreateEndpoint):
    queryset = Models.Run.all.all()
    serializer_class = OfflineRunSerializer
    ALLOWED_METHODS = ["POST"]

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
    ALLOWED_METHODS = ["GET"]

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
