from rest_framework import serializers

from polyaxon.schemas import V1RunResources


class ResourcesMixin(serializers.Serializer):
    def get_resources(self, obj):
        return {
            V1RunResources._MEMORY: obj.memory,
            V1RunResources._CPU: obj.cpu,
            V1RunResources._GPU: obj.gpu,
            V1RunResources._CUSTOM_RESOURCE: obj.custom,
            V1RunResources._COST: obj.cost,
        }
