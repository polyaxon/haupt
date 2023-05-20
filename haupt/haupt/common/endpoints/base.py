from typing import Optional

from clipped.utils.versions import clean_version_for_check
from rest_framework import exceptions
from rest_framework.generics import GenericAPIView

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from haupt.common import auditor, user_system
from haupt.common.apis.gzip import gzip
from haupt.common.apis.regex import OWNER_NAME_KEY, PROJECT_NAME_KEY, UUID_KEY
from haupt.common.authentication.bot import is_bot_user
from haupt.common.authentication.internal import is_internal_user
from haupt.common.endpoints import mixins
from haupt.common.endpoints.exceptions import EndpointError
from haupt.common.headers import get_service_header
from haupt.common.user_system import USER_SYSTEM_ID, USER_SYSTEM_NAME


class BaseEndpoint(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    serializer_class_mapping = None

    AUDITOR_EVENT_TYPES = None
    AUDIT_OWNER = False
    AUDIT_PROJECT = False
    AUDIT_PROJECT_RESOURCES = False
    AUDIT_INSTANCE = False
    AUDIT_EXTRA_KEYS = ()

    PROJECT_NAME_KEY = PROJECT_NAME_KEY
    PROJECT_OWNER_NAME_KEY = OWNER_NAME_KEY
    PROJECT_RESOURCE_KEY = None

    CONTEXT_KEYS = ()
    QUERY_CONTEXT_KEYS = ()
    CONTEXT_OBJECTS = ()

    ALLOWED_METHODS = ()
    ALLOWED_SERVICES = ()
    CHECK_SERVICE = False
    throttle_scope = "user"

    # This is a memoization for get_object, to avoid accidentally calling twice.
    _object = None
    _instance_id = None
    _instance_uuid = None
    _owner_id = None

    def set_owner(self):
        pass

    def get_object(self):
        """We memoize the access to this function in case a second call is made."""
        if self._object:
            return self._object
        self._object = super().get_object()
        return self._object

    def filter_queryset(self, queryset):
        queryset = self.enrich_queryset(queryset=queryset)
        return super().filter_queryset(queryset=queryset)

    def enrich_queryset(self, queryset):
        return queryset

    @staticmethod
    def get_service(request: HttpRequest) -> Optional[str]:
        service = get_service_header(request=request)
        if service:
            try:
                return service.decode()
            except UnicodeError:
                msg = (
                    "Invalid internal_service header. "
                    "internal_service string should not contain invalid characters."
                )
                raise exceptions.AuthenticationFailed(msg)

    @classmethod
    def get_service_version(cls, request: HttpRequest) -> Optional[str]:
        service = cls.get_service(request)
        if not service:
            return None
        service = clean_version_for_check(service)
        return service if len(service.split(".")) >= 3 else None

    @classmethod
    def check_service(cls, request: HttpRequest):
        service = cls.get_service(request=request)

        if (
            cls.CHECK_SERVICE
            and cls.ALLOWED_SERVICES
            and service not in cls.ALLOWED_SERVICES
        ):
            raise exceptions.AuthenticationFailed(
                "Service requesting this endpoint not allowed."
            )

    @classmethod
    def check_method(cls, request: HttpRequest):
        if request.method not in cls.ALLOWED_METHODS:
            raise exceptions.MethodNotAllowed(method=request.method)

    def check_request(self, request: HttpRequest):
        self.check_method(request)
        self.check_service(request)

    @staticmethod
    def check_public_only_access(request):
        return request.access.public_only

    def initialize_context(self, request: HttpRequest, *args, **kwargs):
        """
        Initializes the endpoint with the context keys based on the passed
        and/or based on the query parameters (request.GET).
        """
        self.check_request(request)

        for key in self.CONTEXT_KEYS:
            if key not in kwargs:
                raise EndpointError(
                    f"Endpoint `{self.__class__.__name__}` requires a context key {key}, "
                    f"but it was not found."
                )
            setattr(self, key, kwargs.get(key))
        for key in self.QUERY_CONTEXT_KEYS:
            setattr(self, key, request.query_params.get(key))

        if self.AUDIT_OWNER:
            assert OWNER_NAME_KEY in kwargs
        if self.AUDIT_PROJECT:
            assert PROJECT_NAME_KEY in kwargs
        if self.AUDIT_PROJECT_RESOURCES:
            assert self.PROJECT_RESOURCE_KEY is not None
            assert self.PROJECT_RESOURCE_KEY in kwargs

    def initialize_object_context(self, request: HttpRequest, *args, **kwargs):
        pass

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.initialize_context(request, *args, **kwargs)
        self.initialize_object_context(request, *args, **kwargs)

    def initialize_request(self, request, *args, **kwargs):
        request = super().initialize_request(request, *args, **kwargs)
        request.access = None
        return request

    def get_audit_params(self, **kwargs):
        params = {}
        if self.AUDIT_OWNER:
            params[self.PROJECT_OWNER_NAME_KEY] = kwargs.get(OWNER_NAME_KEY)
        if self.AUDIT_PROJECT:
            params[self.PROJECT_NAME_KEY] = kwargs.get(PROJECT_NAME_KEY)
        if self.AUDIT_PROJECT_RESOURCES:
            params[UUID_KEY] = kwargs.get(self.PROJECT_RESOURCE_KEY)
        if self.AUDIT_INSTANCE:
            params["instance"] = self._object
        for extra_key in self.AUDIT_EXTRA_KEYS:
            params[extra_key] = kwargs.get(extra_key)
        return params

    def get_event_type(self, request) -> Optional[str]:
        event_types = self.AUDITOR_EVENT_TYPES or {}
        event_type = event_types.get(request.method)
        if not settings.HAS_ORG_MANAGEMENT:
            return event_type
        if (
            event_type
            and not user_system.is_system_user(request.user.id)
            and not request.user.is_anonymous
            and not is_bot_user(request.user)
            and not is_internal_user(request.user)
        ):
            return event_type

    def audit_check(self, request):
        return True

    def audit(self, request, *args, **kwargs):
        event_type = self.get_event_type(request)
        if event_type and self.audit_check(request):
            self.set_owner()
            params = self.get_audit_params(**kwargs)
            auditor.record(
                event_type=event_type,
                actor_id=self.request.user.id
                if settings.HAS_ORG_MANAGEMENT
                else USER_SYSTEM_ID,
                actor_name=self.request.user.username
                if settings.HAS_ORG_MANAGEMENT
                else USER_SYSTEM_NAME,
                owner_id=self._owner_id,
                **params,
            )

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.

        You may want to override this if you need to provide different
        serializations depending on the incoming request.

        (Eg. admins get full serialization, others get basic serialization)
        """
        assert (
            self.serializer_class is not None
            or self.serializer_class_mapping is not None
        ), (
            "'%s' should either include a `serializer_class` attribute or "
            "a `serializer_class_mapping` attribute, "
            "or override the `get_serializer_class()` method." % self.__class__.__name__
        )

        if self.serializer_class_mapping:
            return self.serializer_class_mapping[self.request.method]
        return self.serializer_class


class CreateEndpoint:
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return self.create(request, *args, **kwargs)


class PostEndpoint:
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return self.create(request, *args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        pass


class ListEndpoint:
    @gzip()
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return self.list(request, *args, **kwargs)


class RetrieveEndpoint:
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return self.retrieve(request, *args, **kwargs)


class DestroyEndpoint:
    def delete(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return self.destroy(request, *args, **kwargs)


class UpdateEndpoint:
    def put(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return self.update(request, *args, **kwargs)

    def patch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return self.partial_update(request, *args, **kwargs)
