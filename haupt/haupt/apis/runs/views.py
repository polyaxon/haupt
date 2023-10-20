from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from django.conf import settings
from django.http import Http404

from haupt.apis.bookmarks.views import BookmarkCreateView, BookmarkDeleteView
from haupt.apis.endpoints.run import RunEndpoint
from haupt.apis.methods import runs as methods
from haupt.apis.serializers.runs import (
    RunDetailSerializer,
    RunSerializer,
    RunStatusSerializer,
)
from haupt.common import conf
from haupt.common.apis.regex import RUN_UUID_KEY
from haupt.common.content_types import ContentTypes
from haupt.common.endpoints.base import (
    CreateEndpoint,
    DestroyEndpoint,
    PostEndpoint,
    RetrieveEndpoint,
    UpdateEndpoint,
)
from haupt.common.endpoints.mixins import StatsMixin
from haupt.common.events.registry.archive import RUN_ARCHIVED_ACTOR, RUN_RESTORED_ACTOR
from haupt.common.events.registry.bookmark import (
    RUN_BOOKMARKED_ACTOR,
    RUN_UNBOOKMARKED_ACTOR,
)
from haupt.common.events.registry.run import (
    RUN_APPROVED_ACTOR,
    RUN_COPIED_ACTOR,
    RUN_DELETED_ACTOR,
    RUN_INVALIDATED_ACTOR,
    RUN_RESTARTED_ACTOR,
    RUN_RESUMED_ACTOR,
    RUN_SKIPPED_ACTOR,
    RUN_STATS_ACTOR,
    RUN_STOPPED_ACTOR,
    RUN_TRANSFERRED_ACTOR,
)
from haupt.common.options.registry.k8s import K8S_NAMESPACE
from haupt.db.defs import Models
from haupt.db.managers.live_state import delete_in_progress_run
from haupt.db.managers.stats import StatsSerializer
from haupt.db.queries.runs import STATUS_UPDATE_COLUMNS_DEFER
from haupt.orchestration import operations
from polyaxon._services.values import PolyaxonServices
from polyaxon.schemas import LifeCycle, V1CloningKind


class RunDetailView(RunEndpoint, RetrieveEndpoint, DestroyEndpoint, UpdateEndpoint):
    serializer_class = RunDetailSerializer
    AUDITOR_EVENT_TYPES = {
        "DELETE": RUN_DELETED_ACTOR,
    }
    ALLOWED_METHODS = ["GET", "PUT", "PATCH", "DELETE"]
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True
    AUDIT_OWNER = True
    AUDIT_PROJECT = True

    def _get_related_fields(self):
        return ["original", "pipeline", "project"]

    def _get_prefetch_fields(self):
        return []

    def get_queryset(self):
        if self.request.method == "GET":
            prefetch_fields = self._get_prefetch_fields()
            queryset = Models.Run.all.select_related(*self._get_related_fields())
            if prefetch_fields:
                queryset = queryset.prefetch_related(*prefetch_fields)
            return queryset
        return super().get_queryset()

    def perform_destroy(self, instance):
        delete_in_progress_run(instance)


class RunCloneView(RunEndpoint, CreateEndpoint):
    serializer_class = RunSerializer
    ALLOWED_METHODS = ["POST"]
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True
    AUDIT_PROJECT = True
    AUDIT_OWNER = True

    def clone(self, obj, content, **kwargs):
        pass

    def pre_validate(self, obj):
        # Restart/Copy original run
        if obj.cloning_kind == V1CloningKind.CACHE:
            return obj.original
        return obj

    def post(self, request, *args, **kwargs):
        return methods.clone_run(view=self, request=request, *args, **kwargs)


class RunRestartView(RunCloneView):
    AUDITOR_EVENT_TYPES = {"POST": RUN_RESTARTED_ACTOR}

    def _get_Additional_fields(self, obj):
        return {}

    def clone(self, obj, content, **kwargs):
        return operations.restart_run(
            run=obj,
            user_id=self.request.user.id,
            content=content,
            name=kwargs.get("name"),
            description=kwargs.get("description"),
            tags=kwargs.get("tags"),
            meta_info=kwargs.get("meta_info"),
            **self._get_Additional_fields(obj)
        )


class RunResumeView(RunCloneView):
    AUDITOR_EVENT_TYPES = {"POST": RUN_RESUMED_ACTOR}

    def _get_additional_fields(self, obj):
        return {}

    def clone(self, obj, content, **kwargs):
        return operations.resume_run(
            run=obj,
            user_id=self.request.user.id,
            content=content,
            name=kwargs.get("name"),
            description=kwargs.get("description"),
            tags=kwargs.get("tags"),
            meta_info=kwargs.get("meta_info"),
            message="Run was resumed by user.",
            **self._get_additional_fields(obj)
        )

    def pre_validate(self, obj):
        if not LifeCycle.is_done(obj.status):
            raise ValidationError(
                "Cannot resume this run, the run must reach a final state first, "
                "current status error: {}".format(obj.status)
            )

        if obj.cloning_kind == V1CloningKind.CACHE:
            raise ValidationError(
                "Cannot resume this run, this run is a cache hit and was never executed."
            )
        return super().pre_validate(obj)


class RunCopyView(RunCloneView):
    AUDITOR_EVENT_TYPES = {"POST": RUN_COPIED_ACTOR}

    def clone(self, obj, content, **kwargs):
        return operations.copy_run(
            run=obj,
            user_id=self.request.user.id,
            content=content,
            name=kwargs.get("name"),
            description=kwargs.get("description"),
            tags=kwargs.get("tags"),
            meta_info=kwargs.get("meta_info"),
        )


class RunStatusListView(RunEndpoint, RetrieveEndpoint, CreateEndpoint):
    queryset = Models.Run.restorable.defer(*STATUS_UPDATE_COLUMNS_DEFER).select_related(
        "project",
    )
    serializer_class = RunStatusSerializer
    throttle_scope = "run-status"
    ALLOWED_METHODS = ["POST", "GET"]

    def perform_create(self, serializer):
        try:
            methods.create_status(view=self, serializer=serializer)
        except Models.Run.DoesNotExist:
            raise Http404


class RunStopView(RunEndpoint, CreateEndpoint):
    ALLOWED_METHODS = ["POST"]
    AUDITOR_EVENT_TYPES = {"POST": RUN_STOPPED_ACTOR}
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True
    AUDIT_PROJECT_RESOURCES = True
    AUDIT_PROJECT = True
    AUDIT_OWNER = True

    def post(self, request, *args, **kwargs):
        return methods.stop_run(view=self, request=request, *args, **kwargs)


class RunSkipView(RunEndpoint, CreateEndpoint):
    ALLOWED_METHODS = ["POST"]
    AUDITOR_EVENT_TYPES = {"POST": RUN_SKIPPED_ACTOR}
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True
    AUDIT_PROJECT_RESOURCES = True
    AUDIT_PROJECT = True
    AUDIT_OWNER = True

    def post(self, request, *args, **kwargs):
        return methods.skip_run(view=self, request=request, *args, **kwargs)


class RunApproveView(RunEndpoint, CreateEndpoint):
    ALLOWED_METHODS = ["POST"]
    AUDITOR_EVENT_TYPES = {"POST": RUN_APPROVED_ACTOR}
    AUDIT_PROJECT = True
    AUDIT_OWNER = True
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True

    def post(self, request, *args, **kwargs):
        return methods.approve_run(view=self, request=request, *args, **kwargs)


class RunNamespaceView(RunEndpoint, RetrieveEndpoint):
    ALLOWED_METHODS = ["GET"]

    def retrieve(self, request, *args, **kwargs):
        namespace = {"namespace": conf.get(K8S_NAMESPACE)}
        return Response(namespace)


class RunTransferView(RunEndpoint, CreateEndpoint):
    ALLOWED_METHODS = ["POST"]
    AUDITOR_EVENT_TYPES = {"POST": RUN_TRANSFERRED_ACTOR}
    AUDIT_PROJECT = True
    AUDIT_OWNER = True
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True

    def post(self, request, *args, **kwargs):
        return methods.transfer_run(view=self, request=request, *args, **kwargs)


class RunInvalidateView(RunEndpoint, PostEndpoint):
    serializer_class = RunSerializer
    AUDITOR_EVENT_TYPES = {"POST": RUN_INVALIDATED_ACTOR}
    ALLOWED_METHODS = ["POST"]
    AUDIT_PROJECT = True
    AUDIT_OWNER = True
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True

    def post(self, request, *args, **kwargs):
        return methods.invalidate_run(view=self, request=request, *args, **kwargs)


class RunArchiveView(RunEndpoint, PostEndpoint):
    AUDITOR_EVENT_TYPES = {"POST": RUN_ARCHIVED_ACTOR}
    ALLOWED_METHODS = ["POST"]
    AUDIT_PROJECT = True
    AUDIT_OWNER = True
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True

    def post(self, request, *args, **kwargs):
        return methods.archive_run(view=self, request=request, *args, **kwargs)


class RunRestoreView(RunEndpoint, PostEndpoint):
    AUDITOR_EVENT_TYPES = {"POST": RUN_RESTORED_ACTOR}
    ALLOWED_METHODS = ["POST"]
    AUDIT_PROJECT = True
    AUDIT_OWNER = True
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True

    def post(self, request, *args, **kwargs):
        return methods.restore_run(view=self, request=request, *args, **kwargs)


SELECT_RELATED = ["project__owner"] if settings.HAS_ORG_MANAGEMENT else []


class RunBookmarkCreateView(RunEndpoint, BookmarkCreateView):
    queryset = Models.Run.restorable.prefetch_related(*SELECT_RELATED, "project")
    AUDITOR_EVENT_TYPES = {"POST": RUN_BOOKMARKED_ACTOR}
    ALLOWED_METHODS = ["POST"]
    content_type = ContentTypes.RUN.value
    AUDIT_PROJECT = True
    AUDIT_OWNER = True
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True


class RunBookmarkDeleteView(RunEndpoint, BookmarkDeleteView):
    queryset = Models.Run.restorable.prefetch_related(*SELECT_RELATED, "project")
    AUDITOR_EVENT_TYPES = {"DELETE": RUN_UNBOOKMARKED_ACTOR}
    ALLOWED_METHODS = ["DELETE"]
    content_type = ContentTypes.RUN.value
    AUDIT_PROJECT = True
    AUDIT_OWNER = True
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True


class RunStatsView(RunEndpoint, RetrieveEndpoint, StatsMixin):
    AUDITOR_EVENT_TYPES = {
        "GET": RUN_STATS_ACTOR,
    }
    ALLOWED_METHODS = ["GET"]
    ALLOWED_SERVICES = [PolyaxonServices.UI]
    CHECK_SERVICE = True
    AUDIT_PROJECT = True
    AUDIT_OWNER = True
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True
    bookmarked_model = "run"

    def get_serializer(self, *args, **kwargs):
        self.validate_stats_mode()
        queryset = Models.Run.restorable.filter(pipeline_id=self.run.id)
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
