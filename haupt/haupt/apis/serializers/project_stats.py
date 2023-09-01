from rest_framework import serializers

from haupt.db.defs import Models


class StatsUserSerializerMixin(serializers.ModelSerializer):
    LIGHT = True
    user = serializers.SerializerMethodField()

    class Meta:
        fields = (
            "created_at",
            "updated_at",
            "user",
            "run",
            "status",
            "version",
            "tracking_time",
        )

    def get_user(self, obj):
        if not obj.user:
            return obj.user
        if self.LIGHT:
            return {"count": obj.user.get("count", 0)}
        if not obj.user.get("ids"):
            return obj.user
        users = Models.User.objects.filter(id__in=obj.user["ids"]).values_list(
            "username", flat=True
        )
        return {"count": obj.user["count"], "users": list(users)}


class ProjectStatsSerializer(StatsUserSerializerMixin):
    class Meta(StatsUserSerializerMixin.Meta):
        model = Models.ProjectStats
