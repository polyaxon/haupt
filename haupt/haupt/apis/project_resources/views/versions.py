from clipped.utils.versions import compare_versions
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from django.conf import settings
from django.http import Http404

from haupt.apis.endpoints.project import VersionEndpoint, VersionListEndpoint
from haupt.apis.methods import entity_stages as methods
from haupt.apis.serializers.project_versions import (
    ArtifactVersionDetailSerializer,
    ComponentVersionDetailSerializer,
    ModelVersionDetailSerializer,
    ProjectVersionDetailSerializer,
    ProjectVersionNameSerializer,
    ProjectVersionSerializer,
    ProjectVersionStageSerializer,
)
from haupt.common import auditor
from haupt.common.apis.filters import OrderingFilter, QueryFilter
from haupt.common.apis.paginator import LargeLimitOffsetPagination
from haupt.common.endpoints.base import (
    CreateEndpoint,
    DestroyEndpoint,
    ListEndpoint,
    RetrieveEndpoint,
    UpdateEndpoint,
)
from haupt.common.events.registry.artifact_version import (
    ARTIFACT_VERSION_CREATED_ACTOR,
    ARTIFACT_VERSION_DELETED_ACTOR,
    ARTIFACT_VERSION_NEW_STAGE,
    ARTIFACT_VERSION_TRANSFERRED_ACTOR,
    ARTIFACT_VERSION_UPDATED_ACTOR,
    ARTIFACT_VERSION_VIEWED_ACTOR,
)
from haupt.common.events.registry.component_version import (
    COMPONENT_VERSION_CREATED_ACTOR,
    COMPONENT_VERSION_DELETED_ACTOR,
    COMPONENT_VERSION_NEW_STAGE,
    COMPONENT_VERSION_TRANSFERRED_ACTOR,
    COMPONENT_VERSION_UPDATED_ACTOR,
    COMPONENT_VERSION_VIEWED_ACTOR,
)
from haupt.common.events.registry.model_version import (
    MODEL_VERSION_CREATED_ACTOR,
    MODEL_VERSION_DELETED_ACTOR,
    MODEL_VERSION_NEW_STAGE,
    MODEL_VERSION_TRANSFERRED_ACTOR,
    MODEL_VERSION_UPDATED_ACTOR,
    MODEL_VERSION_VIEWED_ACTOR,
)
from haupt.db.defs import Models
from haupt.db.managers.versions import add_version_contributors
from haupt.db.query_managers.project_version import ProjectVersionQueryManager
from polyaxon.schemas import V1ProjectVersionKind

ADDITIONAL_SELECT_RELATED = ["project__owner"] if settings.HAS_ORG_MANAGEMENT else []


class ProjectVersionListView(VersionListEndpoint, ListEndpoint, CreateEndpoint):
    queryset = Models.ProjectVersion.objects.defer("content").order_by("-updated_at")
    filter_backends = (QueryFilter, OrderingFilter)
    query_manager = ProjectVersionQueryManager
    check_alive = ProjectVersionQueryManager.CHECK_ALIVE
    ordering = ProjectVersionQueryManager.FIELDS_DEFAULT_ORDERING
    ordering_fields = ProjectVersionQueryManager.FIELDS_ORDERING
    ordering_proxy_fields = ProjectVersionQueryManager.FIELDS_ORDERING_PROXY
    AUDIT_OWNER = True
    AUDIT_PROJECT = True
    AUDIT_INSTANCE = True
    ALLOWED_METHODS = ["GET", "POST"]
    EVENTS_TYPE = None

    def perform_create(self, serializer):
        instance = serializer.save(project=self.project)
        if not self.EVENTS_TYPE:
            return
        add_version_contributors(instance, users=[self.request.user])
        auditor.record(
            event_type=self.EVENTS_TYPE,
            instance=instance,
            actor_id=self.request.user.id,
            actor_name=self.request.user.username,
            owner_id=self.project.owner_id,
            owner_name=self.owner_name,
            hub_name=self.project_name,
        )


class ProjectComponentVersionListView(ProjectVersionListView):
    serializer_class_mapping = {
        "GET": ProjectVersionSerializer,
        "POST": ComponentVersionDetailSerializer,
    }
    EVENTS_TYPE = COMPONENT_VERSION_CREATED_ACTOR
    queryset = (
        Models.ProjectVersion.objects.filter(kind=V1ProjectVersionKind.COMPONENT)
        .defer("content")
        .order_by("-updated_at")
    )


class ProjectModelVersionListView(ProjectVersionListView):
    serializer_class_mapping = {
        "GET": ProjectVersionSerializer,
        "POST": ModelVersionDetailSerializer,
    }
    EVENTS_TYPE = MODEL_VERSION_CREATED_ACTOR
    queryset = (
        Models.ProjectVersion.objects.filter(kind=V1ProjectVersionKind.MODEL)
        .defer("content")
        .order_by("-updated_at")
    )


class ProjectArtifactVersionListView(ProjectVersionListView):
    serializer_class_mapping = {
        "GET": ProjectVersionSerializer,
        "POST": ArtifactVersionDetailSerializer,
    }
    EVENTS_TYPE = ARTIFACT_VERSION_CREATED_ACTOR
    queryset = (
        Models.ProjectVersion.objects.filter(kind=V1ProjectVersionKind.ARTIFACT)
        .defer("content")
        .order_by("-updated_at")
    )


class ProjectVersionNameListView(VersionListEndpoint, ListEndpoint):
    """List project versions' names for a user."""

    queryset = Models.ProjectVersion.objects.only("name").order_by("-updated_at")
    filter_backends = (QueryFilter, OrderingFilter)
    query_manager = ProjectVersionQueryManager
    check_alive = ProjectVersionQueryManager.CHECK_ALIVE
    ordering = ProjectVersionQueryManager.FIELDS_DEFAULT_ORDERING
    ordering_fields = ProjectVersionQueryManager.FIELDS_ORDERING
    ordering_proxy_fields = ProjectVersionQueryManager.FIELDS_ORDERING_PROXY
    serializer_class = ProjectVersionNameSerializer
    pagination_class = LargeLimitOffsetPagination
    ALLOWED_METHODS = ["GET"]


class ProjectComponentVersionNameListView(ProjectVersionNameListView):
    queryset = (
        Models.ProjectVersion.objects.filter(kind=V1ProjectVersionKind.COMPONENT)
        .only("name")
        .order_by("-updated_at")
    )


class ProjectModelVersionNameListView(ProjectVersionNameListView):
    queryset = (
        Models.ProjectVersion.objects.filter(kind=V1ProjectVersionKind.MODEL)
        .only("name")
        .order_by("-updated_at")
    )


class ProjectArtifactVersionNameListView(ProjectVersionNameListView):
    queryset = (
        Models.ProjectVersion.objects.filter(kind=V1ProjectVersionKind.ARTIFACT)
        .only("name")
        .order_by("-updated_at")
    )


ADDITIONAL_SELECT_RELATED_DETAILS = ADDITIONAL_SELECT_RELATED + (
    [
        "connection",
        "connection__agent",
    ]
    if settings.HAS_ORG_MANAGEMENT
    else []
)
ADDITIONAL_PREFETCH_RELATED_DETAILS = (
    [
        "contributors",
        "lineage__connection",
    ]
    if settings.HAS_ORG_MANAGEMENT
    else []
)


class ProjectVersionDetailView(
    VersionEndpoint, RetrieveEndpoint, UpdateEndpoint, DestroyEndpoint
):
    """
    get:
        Get a project version details.
    patch:
        Update a project version details.
    delete:
        Delete a project version.
    """

    queryset = Models.ProjectVersion.objects.select_related(
        *ADDITIONAL_SELECT_RELATED_DETAILS,
        "project",
        "run",
        "run__project",
    ).prefetch_related(
        *ADDITIONAL_PREFETCH_RELATED_DETAILS,
        "lineage",
        "lineage__artifact",
    )
    ALLOWED_METHODS = ["GET", "PUT", "PATCH", "DELETE"]
    AUDIT_OWNER = True
    AUDIT_PROJECT = True
    AUDIT_INSTANCE = True

    def get_serializer(self, *args, **kwargs):
        service = self.get_service(request=self.request)
        service_version = self.get_service_version(request=self.request)
        if not service:
            compatibility = "both"
        elif service_version and compare_versions(
            current=service_version, reference="1.18.0", comparator="<"
        ):
            compatibility = "old"
        else:
            compatibility = "new"

        serializer_class = self.get_serializer_class()
        context = self.get_serializer_context()
        context["compatibility"] = compatibility
        kwargs["context"] = context
        return serializer_class(*args, **kwargs)

    def perform_update(self, serializer):
        instance = serializer.save()
        add_version_contributors(instance, users=[self.request.user])


class ProjectComponentVersionDetailView(ProjectVersionDetailView):
    serializer_class_mapping = {
        "GET": ProjectVersionDetailSerializer,
        "DELETE": ProjectVersionDetailSerializer,
        "PATCH": ComponentVersionDetailSerializer,
        "PUT": ComponentVersionDetailSerializer,
    }
    queryset = ProjectVersionDetailView.queryset.filter(
        kind=V1ProjectVersionKind.COMPONENT
    )
    AUDITOR_EVENT_TYPES = {
        "GET": COMPONENT_VERSION_VIEWED_ACTOR,
        "PUT": COMPONENT_VERSION_UPDATED_ACTOR,
        "PATCH": COMPONENT_VERSION_UPDATED_ACTOR,
        "DELETE": COMPONENT_VERSION_DELETED_ACTOR,
    }


class ProjectModelVersionDetailView(ProjectVersionDetailView):
    serializer_class_mapping = {
        "GET": ProjectVersionDetailSerializer,
        "DELETE": ProjectVersionDetailSerializer,
        "PATCH": ModelVersionDetailSerializer,
        "PUT": ModelVersionDetailSerializer,
    }
    queryset = ProjectVersionDetailView.queryset.filter(kind=V1ProjectVersionKind.MODEL)
    AUDITOR_EVENT_TYPES = {
        "GET": MODEL_VERSION_VIEWED_ACTOR,
        "PUT": MODEL_VERSION_UPDATED_ACTOR,
        "PATCH": MODEL_VERSION_UPDATED_ACTOR,
        "DELETE": MODEL_VERSION_DELETED_ACTOR,
    }


class ProjectArtifactVersionDetailView(ProjectVersionDetailView):
    serializer_class_mapping = {
        "GET": ProjectVersionDetailSerializer,
        "DELETE": ProjectVersionDetailSerializer,
        "PATCH": ArtifactVersionDetailSerializer,
        "PUT": ArtifactVersionDetailSerializer,
    }
    queryset = ProjectVersionDetailView.queryset.filter(
        kind=V1ProjectVersionKind.ARTIFACT
    )
    AUDITOR_EVENT_TYPES = {
        "GET": ARTIFACT_VERSION_VIEWED_ACTOR,
        "PUT": ARTIFACT_VERSION_UPDATED_ACTOR,
        "PATCH": ARTIFACT_VERSION_UPDATED_ACTOR,
        "DELETE": ARTIFACT_VERSION_DELETED_ACTOR,
    }


class ProjectVersionTransferView(VersionEndpoint, CreateEndpoint):
    queryset = Models.ProjectVersion.objects.defer(
        "content", "description"
    ).select_related(
        *ADDITIONAL_SELECT_RELATED,
        "project",
    )
    ALLOWED_METHODS = ["POST"]
    AUDIT_OWNER = True
    AUDIT_PROJECT = True
    AUDIT_INSTANCE = True

    def post(self, request, *args, **kwargs):
        project_name = request.data.get("project")
        if project_name == self.project_name:
            return Response(status=status.HTTP_200_OK, data={})
        if not project_name:
            raise ValidationError("The destination project was not provided.")
        try:
            org_filters = (
                dict(owner__name=self.owner_name) if settings.HAS_ORG_MANAGEMENT else {}
            )
            dest_project = Models.Project.objects.only("id").get(
                **org_filters, name=project_name
            )
        except Models.Project.DoesNotExist:
            raise ValidationError(
                "The destination project `{}` does not exist.".format(project_name)
            )

        self.version.project_id = dest_project.id
        self.version.save(update_fields=["project_id", "updated_at"])
        add_version_contributors(self.version, users=[request.user])
        self.audit(request, *args, **kwargs)
        return Response(status=status.HTTP_200_OK, data={})


class ProjectComponentVersionTransferView(ProjectVersionTransferView):
    queryset = (
        Models.ProjectVersion.objects.filter(kind=V1ProjectVersionKind.COMPONENT)
        .defer("content", "description")
        .select_related(*ADDITIONAL_SELECT_RELATED, "project")
    )
    AUDITOR_EVENT_TYPES = {"POST": COMPONENT_VERSION_TRANSFERRED_ACTOR}


class ProjectModelVersionTransferView(ProjectVersionTransferView):
    queryset = (
        Models.ProjectVersion.objects.filter(kind=V1ProjectVersionKind.MODEL)
        .defer("content", "description")
        .select_related(
            *ADDITIONAL_SELECT_RELATED,
            "project",
        )
    )
    AUDITOR_EVENT_TYPES = {"POST": MODEL_VERSION_TRANSFERRED_ACTOR}


class ProjectArtifactVersionTransferView(ProjectVersionTransferView):
    queryset = (
        Models.ProjectVersion.objects.filter(kind=V1ProjectVersionKind.ARTIFACT)
        .defer("content", "description")
        .select_related(
            *ADDITIONAL_SELECT_RELATED,
            "project",
        )
    )
    AUDITOR_EVENT_TYPES = {"POST": ARTIFACT_VERSION_TRANSFERRED_ACTOR}


class ProjectVersionStageListView(VersionEndpoint, RetrieveEndpoint, CreateEndpoint):
    queryset = Models.ProjectVersion.objects.defer(
        "content", "description"
    ).select_related(
        *ADDITIONAL_SELECT_RELATED,
        "project",
    )
    serializer_class = ProjectVersionStageSerializer
    ALLOWED_METHODS = ["POST", "GET"]

    def perform_create(self, serializer):
        try:
            methods.create_stage(
                view=self,
                serializer=serializer,
                event_type=self.get_event_type(self.request),
            )
        except Models.ProjectVersion.DoesNotExist:
            raise Http404


class ProjectComponentVersionStageListView(ProjectVersionStageListView):
    queryset = (
        Models.ProjectVersion.objects.filter(kind=V1ProjectVersionKind.COMPONENT)
        .defer("content", "description")
        .select_related(
            *ADDITIONAL_SELECT_RELATED,
            "project",
        )
    )
    AUDITOR_EVENT_TYPES = {"POST": COMPONENT_VERSION_NEW_STAGE}


class ProjectModelVersionStageListView(ProjectVersionStageListView):
    queryset = (
        Models.ProjectVersion.objects.filter(kind=V1ProjectVersionKind.MODEL)
        .defer("content", "description")
        .select_related(
            *ADDITIONAL_SELECT_RELATED,
            "project",
        )
    )
    AUDITOR_EVENT_TYPES = {"POST": MODEL_VERSION_NEW_STAGE}


class ProjectArtifactVersionStageListView(ProjectVersionStageListView):
    queryset = (
        Models.ProjectVersion.objects.filter(kind=V1ProjectVersionKind.ARTIFACT)
        .defer("content", "description")
        .select_related(
            *ADDITIONAL_SELECT_RELATED,
            "project",
        )
    )
    AUDITOR_EVENT_TYPES = {"POST": ARTIFACT_VERSION_NEW_STAGE}
