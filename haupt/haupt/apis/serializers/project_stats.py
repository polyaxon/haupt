from rest_framework import serializers

from haupt.db.defs import Models


class StatsUserSerializerMixin(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        if not obj.user or not obj.user.get("ids"):
            return obj.user
        users = Models.User.objects.filter(id__in=obj.user["ids"]).values_list(
            "username", flat=True
        )
        return {"count": obj.user["count"], "users": list(users)}


class ProjectStatsSerializer(StatsUserSerializerMixin):
    class Meta:
        model = Models.ProjectStats
        fields = (
            "created_at",
            "user",
            "run",
            "version",
            "tracking_time",
        )
