from rest_framework import fields, serializers


class ProjectOwnerMixin(serializers.Serializer):
    owner = fields.SerializerMethodField()

    def get_owner(self, obj):
        return obj.project.owner.name
