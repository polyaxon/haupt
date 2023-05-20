from rest_framework import serializers

from haupt.common import conf
from haupt.common.options.registry.k8s import K8S_NAMESPACE


class SettingsMixin:
    settings = serializers.SerializerMethodField()

    def get_settings(self, obj):
        return {
            "namespace": obj.namespace
            if hasattr(obj, "namespace")
            else conf.get(K8S_NAMESPACE),
            "component": {"state": obj.component_state.hex}
            if hasattr(obj, "component_state") and obj.component_state
            else None,
        }
