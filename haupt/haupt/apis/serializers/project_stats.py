from collections import namedtuple

from rest_framework import serializers

from haupt.db.defs import Models


def get_stats(obj):
    stats = {}
    if hasattr(obj, "count"):
        stats["count"] = getattr(obj, "count", 0)
    if hasattr(obj, "pending"):
        stats["pending"] = getattr(obj, "pending", 0)
    if hasattr(obj, "running"):
        stats["running"] = getattr(obj, "running", 0)
    if hasattr(obj, "warning"):
        stats["warning"] = getattr(obj, "warning", 0)
    if hasattr(obj, "cost"):
        stats["cost"] = getattr(obj, "cost", 0)
    if hasattr(obj, "custom"):
        stats["custom"] = getattr(obj, "custom", 0)
    if hasattr(obj, "memory"):
        stats["memory"] = getattr(obj, "memory", 0)
    if hasattr(obj, "cpu"):
        stats["cpu"] = getattr(obj, "cpu", 0)
    if hasattr(obj, "gpu"):
        stats["gpu"] = getattr(obj, "gpu", 0)
    return stats


class RealTimeStats(namedtuple("RealTimeStats", "data")):
    pass


class StatsUserSerializerMixin(serializers.ModelSerializer):
    LIGHT = True
    user = serializers.SerializerMethodField()

    class Meta:
        base_fields = (
            "created_at",
            "updated_at",
            "user",
            "run",
            "status",
            "tracking_time",
            "wait_time",
            "resources",
        )
        fields = base_fields + ("version",)

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
