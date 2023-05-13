from rest_framework import fields, serializers


class ProjectMixin(serializers.Serializer):
    project = fields.SerializerMethodField()

    def get_project(self, obj):
        return obj.project.name
