from haupt.apis.endpoints.run import RunArtifactEndpoint, RunResourceListEndpoint
from haupt.apis.methods import run_lineage as methods
from haupt.apis.serializers.artifacts import (
    RunArtifactNameSerializer,
    RunArtifactSerializer,
)
from haupt.apis.serializers.runs import (
    DownstreamRunEdgeSerializer,
    RunCloneSerializer,
    UpstreamRunEdgeSerializer,
)
from haupt.common.apis.filters import OrderingFilter, QueryFilter
from haupt.common.apis.paginator import LargeLimitOffsetPagination
from haupt.common.apis.regex import RUN_UUID_KEY
from haupt.common.endpoints.base import (
    CreateEndpoint,
    DestroyEndpoint,
    ListEndpoint,
    PostEndpoint,
    RetrieveEndpoint,
)
from haupt.common.events.registry.run import RUN_LINEAGE_ACTOR, RUN_NEW_ARTIFACTS
from haupt.db.defs import Models
from haupt.db.queries import artifacts as artifacts_queries
from haupt.db.query_managers.artifact import ArtifactQueryManager
from haupt.db.query_managers.run import RunQueryManager
from haupt.db.query_managers.run_edge import RunEdgeQueryManager


class RunArtifactListView(RunResourceListEndpoint, ListEndpoint, CreateEndpoint):
    queryset = artifacts_queries.artifacts
    serializer_class = RunArtifactSerializer
    pagination_class = LargeLimitOffsetPagination
    throttle_scope = "run-lineage"
    ALLOWED_METHODS = ["GET", "POST"]
    AUDITOR_EVENT_TYPES = {
        "POST": RUN_NEW_ARTIFACTS,
    }
    AUDIT_OWNER = True
    AUDIT_PROJECT = True
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
        return methods.set_artifacts(view=self, request=request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["run"] = self.run
        return context


class RunArtifactNameListView(RunResourceListEndpoint, ListEndpoint):
    queryset = artifacts_queries.artifacts_names
    serializer_class = RunArtifactNameSerializer
    pagination_class = LargeLimitOffsetPagination
    ALLOWED_METHODS = ["GET"]


class RunEdgeListView(RunResourceListEndpoint, ListEndpoint):
    ALLOWED_METHODS = ["GET"]
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    filter_backends = (QueryFilter, OrderingFilter)
    query_manager = RunEdgeQueryManager
    check_alive = RunEdgeQueryManager.CHECK_ALIVE
    ordering_fields = RunEdgeQueryManager.FIELDS_ORDERING
    ordering_proxy_fields = RunEdgeQueryManager.FIELDS_ORDERING_PROXY


class RunUpstreamListView(RunEdgeListView):
    queryset = Models.RunEdge.objects.prefetch_related("upstream").only(
        "values",
        "kind",
        "statuses",
        "upstream__id",
        "upstream__uuid",
        "upstream__name",
        "upstream__kind",
        "upstream__runtime",
    )
    serializer_class = UpstreamRunEdgeSerializer

    def enrich_queryset(self, queryset):
        return queryset.filter(downstream=self.run)


class RunDownstreamListView(RunEdgeListView):
    queryset = Models.RunEdge.objects.prefetch_related("downstream").only(
        "values",
        "kind",
        "statuses",
        "downstream__id",
        "downstream__uuid",
        "downstream__name",
        "downstream__kind",
        "downstream__runtime",
    )
    serializer_class = DownstreamRunEdgeSerializer

    def enrich_queryset(self, queryset):
        return queryset.filter(upstream=self.run)


class SetRunEdgesLineageView(RunResourceListEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]
    AUDITOR_EVENT_TYPES = {"POST": RUN_LINEAGE_ACTOR}
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_OWNER = True
    AUDIT_PROJECT = True
    AUDIT_PROJECT_RESOURCES = True
    AUDIT_INSTANCE = True

    def create(self, request, *args, **kwargs):
        return methods.set_edges(view=self, request=request, *args, **kwargs)


class RunClonesListView(RunEdgeListView):
    queryset = Models.Run.objects.only(
        "id",
        "uuid",
        "name",
        "kind",
        "runtime",
        "cloning_kind",
        "status",
    )
    filter_backends = (QueryFilter, OrderingFilter)
    query_manager = RunQueryManager
    check_alive = RunQueryManager.CHECK_ALIVE
    ordering_fields = RunQueryManager.FIELDS_ORDERING
    ordering_proxy_fields = RunQueryManager.FIELDS_ORDERING_PROXY
    serializer_class = RunCloneSerializer

    def enrich_queryset(self, queryset):
        return queryset.filter(original=self.run)


class RunArtifactDetailView(RunArtifactEndpoint, RetrieveEndpoint, DestroyEndpoint):
    queryset = artifacts_queries.artifacts
    serializer_class = RunArtifactSerializer
    ALLOWED_METHODS = ["GET", "DELETE"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["run"] = self.run_artifact.run
        return context
