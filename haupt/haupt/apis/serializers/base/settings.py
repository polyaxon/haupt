from rest_framework import serializers

from haupt.common import conf
from haupt.common.options.registry.k8s import K8S_NAMESPACE


class SettingsMixin:
    settings = serializers.SerializerMethodField()

    def get_settings(self, obj):
        return {"namespace": conf.get(K8S_NAMESPACE)}
