from haupt.db.administration.utils import DiffModelAdmin, ReadOnlyAdmin


class RunLightAdmin(DiffModelAdmin, ReadOnlyAdmin):
    list_display = (
        "uuid",
        "user",
        "project",
        "name",
        "status",
        "created_at",
        "updated_at",
        "started_at",
        "finished_at",
    )
    fields = (
        "project",
        "name",
        "description",
        "status",
        "live_state",
        "created_at",
        "updated_at",
        "started_at",
        "finished_at",
    )
    readonly_fields = ("status",)
