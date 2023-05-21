from functools import reduce
from operator import or_

from rest_framework import serializers

from django.conf import settings
from django.db.models import Q

from haupt.common import conf
from haupt.common.options.registry.k8s import K8S_NAMESPACE
from haupt.db.defs import Models
from polyaxon.constants.globals import DEFAULT_HUB
from polyaxon.lifecycle import V1ProjectVersionKind
from polyaxon.polyflow import V1RunEdgeKind, V1RunKind


class SettingsMixin:
    settings = serializers.SerializerMethodField()

    def get_settings(self, obj):
        return {
            "namespace": obj.namespace
            if hasattr(obj, "namespace")
            else conf.get(K8S_NAMESPACE),
            "component": {"state": obj.component_state.hex}
            if obj.component_state
            else None,
        }


class FullSettingsMixin:
    def get_settings(self, obj):
        tensorboard = None
        if obj.kind == V1RunKind.JOB:
            tensorboard = (
                obj.downstream_runs.filter(upstream_edges__kind=V1RunEdgeKind.TB)
                .order_by("created_at")
                .last()
            )
        build = (
            obj.upstream_runs.filter(downstream_edges__kind=V1RunEdgeKind.BUILD)
            .order_by("created_at")
            .last()
        )
        filters = [Q(run=obj)]
        if obj.component_state:
            filters.append(Q(state=obj.component_state))
        versions = Models.ProjectVersion.objects
        additional_values = []
        if settings.HAS_ORG_MANAGEMENT:
            additional_values = ["project__owner__name"]
            versions = versions.filter(
                Q(project__owner__id=obj.project.owner_id)
                | Q(project__owner__name=DEFAULT_HUB)
            )
        versions = versions.filter(reduce(or_, filters)).values(
            *additional_values, "project__name", "name", "kind", "state"
        )
        models = []
        artifacts = []
        components = []

        for v in versions:
            k = v.pop("kind")
            v["project"] = v.pop("project__name")
            v["owner"] = v.pop("project__owner__name", "default")
            if k == V1ProjectVersionKind.ARTIFACT:
                artifacts.append(v)
            elif k == V1ProjectVersionKind.MODEL:
                models.append(v)
            elif k == V1ProjectVersionKind.COMPONENT:
                components.append(v)

        return {
            "namespace": obj.namespace
            if hasattr(obj, "namespace")
            else conf.get(K8S_NAMESPACE),
            "agent": {"name": obj.agent.name}
            if hasattr(obj, "agent") and obj.agent and obj.agent.name
            else None,
            "queue": {"name": obj.queue.name}
            if hasattr(obj, "queue") and obj.queue and obj.queue.name
            else None,
            "artifacts_store": {"name": obj.artifacts_store.name}
            if hasattr(obj, "artifacts_store")
            and obj.artifacts_store
            and obj.artifacts_store.name
            else None,
            "tensorboard": {
                "name": tensorboard.name,
                "status": tensorboard.status,
                "uuid": tensorboard.uuid.hex,
            }
            if tensorboard
            else None,
            "build": {
                "name": build.name,
                "status": build.status,
                "uuid": build.uuid.hex,
            }
            if build
            else None,
            "component": {
                "state": obj.component_state.hex,
                "versions": components,
                "count": Models.Run.objects.filter(
                    project_id=obj.project_id,
                    component_state=obj.component_state,
                ).count(),
            }
            if obj.component_state
            else None,
            "models": models,
            "artifacts": artifacts,
        }
