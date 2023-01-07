#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from django.http import Http404

from haupt.apis.endpoints.run import RunEndpoint
from haupt.apis.methods import runs as methods
from haupt.apis.serializers.runs import (
    RunDetailSerializer,
    RunSerializer,
    RunStatusSerializer,
)
from haupt.common import conf
from haupt.common.apis.regex import RUN_UUID_KEY
from haupt.common.endpoints.base import (
    CreateEndpoint,
    DestroyEndpoint,
    RetrieveEndpoint,
    UpdateEndpoint,
)
from haupt.common.events.registry.run import (
    RUN_APPROVED_ACTOR,
    RUN_COPIED_ACTOR,
    RUN_DELETED_ACTOR,
    RUN_RESTARTED_ACTOR,
    RUN_RESUMED_ACTOR,
    RUN_STOPPED_ACTOR,
)
from haupt.common.options.registry.k8s import K8S_NAMESPACE
from haupt.db.queries import runs as runs_queries
from haupt.db.queries.runs import STATUS_UPDATE_COLUMNS_DEFER
from haupt.orchestration import operations
from polyaxon.lifecycle import LifeCycle


class RunDetailView(RunEndpoint, RetrieveEndpoint, DestroyEndpoint, UpdateEndpoint):
    queryset = runs_queries.run_model.all.select_related("original", "project")
    serializer_class = RunDetailSerializer
    AUDITOR_EVENT_TYPES = {
        "DELETE": RUN_DELETED_ACTOR,
    }
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True

    def perform_destroy(self, instance):
        # Deletion managed by the handler
        pass


class RunCloneView(RunEndpoint, CreateEndpoint):
    serializer_class = RunSerializer
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True

    def clone(self, obj, content, **kwargs):
        pass

    def pre_validate(self, obj):
        return obj

    def post(self, request, *args, **kwargs):
        return methods.clone_run(view=self, request=request, *args, **kwargs)


class RunRestartView(RunCloneView):
    AUDITOR_EVENT_TYPES = {"POST": RUN_RESTARTED_ACTOR}

    def clone(self, obj, content, **kwargs):
        return operations.restart_run(
            run=obj,
            user_id=self.request.user.id,
            content=content,
            name=kwargs.get("name"),
            description=kwargs.get("description"),
            tags=kwargs.get("tags"),
        )


class RunResumeView(RunCloneView):
    AUDITOR_EVENT_TYPES = {"POST": RUN_RESUMED_ACTOR}

    def clone(self, obj, content, **kwargs):
        return operations.resume_run(
            run=obj,
            user_id=self.request.user.id,
            content=content,
            message="Run was resumed by user.",
        )

    def pre_validate(self, obj):
        if not LifeCycle.is_done(obj.status):
            raise ValidationError(
                "Cannot resume this run, the run must reach a final state first, "
                "current status error: {}".format(obj.status)
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
    queryset = runs_queries.run_model.restorable.defer(
        *STATUS_UPDATE_COLUMNS_DEFER
    ).select_related(
        "project",
    )
    serializer_class = RunStatusSerializer

    def perform_create(self, serializer):
        try:
            methods.create_status(view=self, serializer=serializer)
        except runs_queries.run_model.DoesNotExit:
            raise Http404


class RunStopView(RunEndpoint, CreateEndpoint):
    AUDITOR_EVENT_TYPES = {"POST": RUN_STOPPED_ACTOR}
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True

    def post(self, request, *args, **kwargs):
        return methods.stop_run(view=self, request=request, *args, **kwargs)


class RunApproveView(RunEndpoint, CreateEndpoint):
    AUDITOR_EVENT_TYPES = {"POST": RUN_APPROVED_ACTOR}
    AUDIT_PROJECT_RESOURCES = True
    PROJECT_RESOURCE_KEY = RUN_UUID_KEY
    AUDIT_INSTANCE = True

    def post(self, request, *args, **kwargs):
        return methods.approve_run(view=self, request=request, *args, **kwargs)


class RunNamespaceView(RunEndpoint, RetrieveEndpoint):
    def retrieve(self, request, *args, **kwargs):
        namespace = {"namespace": conf.get(K8S_NAMESPACE)}
        return Response(namespace)
