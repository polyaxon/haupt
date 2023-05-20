from django.conf import settings
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
from haupt.common.permissions import PERMISSIONS_MAPPING
from haupt.db.defs import Models


class RunEndpoint(ProjectResourceEndpoint):
    queryset = (
        Models.Run.all.select_related("project", "project__owner")
        if settings.HAS_ORG_MANAGEMENT
        else Models.Run.all.select_related("project")
    )
    lookup_field = UUID_KEY
    lookup_url_kwarg = RUN_UUID_KEY
    permission_classes = PERMISSIONS_MAPPING.get(["RUN_PERMISSION"])
    throttle_scope = "run"
    CONTEXT_KEYS = (OWNER_NAME_KEY, PROJECT_NAME_KEY, RUN_UUID_KEY)
    CONTEXT_OBJECTS = ("run",)

    def enrich_queryset(self, queryset):
        filters = {"project__name": self.project_name}
        if settings.HAS_ORG_MANAGEMENT:
            filters["project__owner__name"] = self.owner_name
        return queryset.filter(**filters)

    def set_owner(self):
        self.project = self.run.project
        self._owner_id = self.project.owner_id

    def initialize_object_context(self, request: HttpRequest, *args, **kwargs):
        #  pylint:disable=attribute-defined-outside-init
        self.run = self.get_object()


class RunResourceListEndpoint(RunEndpoint):
    permission_classes = PERMISSIONS_MAPPING.get(["RUN_PERMISSION"])
    AUDITOR_EVENT_TYPES = None

    def get_object(self):
        if self._object:
            return self._object

        filters = {"uuid": self.run_uuid, "project__name": self.project_name}
        if settings.HAS_ORG_MANAGEMENT:
            filters["project__owner__name"] = self.owner_name
        self._object = get_object_or_404(
            Models.Run.restorable.select_related("project"),
            **filters,
        )

        # May raise a permission denied
        self.check_object_permissions(self.request, self._object)

        return self._object

    def enrich_queryset(self, queryset):
        return queryset.filter(run=self.run)


class RunArtifactEndpoint(RunEndpoint):
    lookup_field = NAME_KEY
    lookup_url_kwarg = ARTIFACT_NAME_KEY
    permission_classes = PERMISSIONS_MAPPING.get(["RUN_RESOURCE_PERMISSION"])
    AUDITOR_EVENT_TYPES = None
    CONTEXT_KEYS = (OWNER_NAME_KEY, PROJECT_NAME_KEY, RUN_UUID_KEY, ARTIFACT_NAME_KEY)
    CONTEXT_OBJECTS = ("run_artifact",)

    def enrich_queryset(self, queryset):
        filters = {"run__uuid": self.run_uuid, "run__project__name": self.project_name}
        if settings.HAS_ORG_MANAGEMENT:
            filters["run__project__owner__name"] = self.owner_name
        return queryset.filter(**filters)

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
        except Models.ArtifactLineage.DoesNotExist:
            raise Http404(
                "No %s matches the given query." % self.queryset.model._meta.object_name
            )
