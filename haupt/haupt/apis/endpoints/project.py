from rest_framework.generics import get_object_or_404

from django.conf import settings
from django.http import HttpRequest

from haupt.common.apis.regex import (
    NAME_KEY,
    OWNER_NAME_KEY,
    PROJECT_NAME_KEY,
    PROJECT_OWNER_NAME_KEY,
    UUID_KEY,
    VERSION_NAME_KEY,
)
from haupt.common.endpoints.base import BaseEndpoint
from haupt.common.permissions import PERMISSIONS_MAPPING
from haupt.db.defs import Models
from polyaxon.schemas import LiveState


class ProjectEndpoint(BaseEndpoint):
    queryset = (
        Models.Project.all.select_related("owner")
        if settings.HAS_ORG_MANAGEMENT
        else Models.Project.all
    )
    lookup_field = NAME_KEY
    lookup_url_kwarg = PROJECT_NAME_KEY
    permission_classes = PERMISSIONS_MAPPING.get(["PROJECT_PERMISSION"])
    CONTEXT_KEYS = (OWNER_NAME_KEY, PROJECT_NAME_KEY)
    CONTEXT_OBJECTS = ("project",)

    PROJECT_NAME_KEY = "name"
    PROJECT_OWNER_NAME_KEY = OWNER_NAME_KEY

    def enrich_queryset(self, queryset):
        if settings.HAS_ORG_MANAGEMENT:
            return queryset.filter(owner__name=self.owner_name)
        return queryset

    def initialize_object_context(self, request: HttpRequest, *args, **kwargs):
        #  pylint:disable=attribute-defined-outside-init
        self.project = self.get_object()

    def set_owner(self):
        self._owner_id = self.project.owner.id


class ProjectResourceListEndpoint(ProjectEndpoint):
    permission_classes = PERMISSIONS_MAPPING.get(["PROJECT_RESOURCE_PERMISSION"])
    AUDITOR_EVENT_TYPES = None

    def _get_object(self):
        filters = {"name": self.project_name}
        if settings.HAS_ORG_MANAGEMENT:
            filters["owner__name"] = self.owner_name
            filters["owner__live_state"] = LiveState.LIVE
        return get_object_or_404(
            Models.Project,
            **filters,
        )

    def get_object(self):
        if self._object:
            return self._object
        self._object = self._get_object()
        if self.permission_classes:
            permission = self.permission_classes[0]()
            cond = permission.has_object_permission(
                request=self.request, view=self, obj=self._object
            )
            if not cond:
                self.permission_denied(
                    self.request, message=getattr(permission, "message", None)
                )
        return self._object

    def enrich_queryset(self, queryset):
        return queryset.filter(project=self.project)


class ProjectResourceEndpoint(ProjectEndpoint):
    permission_classes = PERMISSIONS_MAPPING.get(["PROJECT_RESOURCE_PERMISSION"])
    lookup_field = UUID_KEY
    AUDITOR_EVENT_TYPES = None

    PROJECT_NAME_KEY = PROJECT_NAME_KEY
    PROJECT_OWNER_NAME_KEY = PROJECT_OWNER_NAME_KEY


class VersionListEndpoint(ProjectResourceListEndpoint):
    pass


class VersionEndpoint(ProjectResourceEndpoint):
    permission_classes = PERMISSIONS_MAPPING.get(["PROJECT_VERSION_PERMISSION"])
    lookup_field = NAME_KEY
    lookup_url_kwarg = VERSION_NAME_KEY
    CONTEXT_KEYS = (OWNER_NAME_KEY, PROJECT_NAME_KEY, VERSION_NAME_KEY)
    CONTEXT_OBJECTS = ("version",)

    def enrich_queryset(self, queryset):
        org_filters = (
            {"project__owner__name": self.owner_name}
            if settings.HAS_ORG_MANAGEMENT
            else {}
        )
        return queryset.filter(project__name=self.project_name, **org_filters)

    def set_owner(self):
        self._owner_id = self.version.project.owner_id

    def initialize_object_context(self, request: HttpRequest, *args, **kwargs) -> None:
        #  pylint:disable=attribute-defined-outside-init
        self.version = self.get_object()
        self.set_owner()
