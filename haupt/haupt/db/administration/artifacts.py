from haupt.db.administration.utils import DiffModelAdmin


class ArtifactAdmin(DiffModelAdmin):
    list_display = (
        "name",
        "kind",
        "state",
    )
    list_display_links = (
        "name",
        "kind",
        "state",
    )
    readonly_fields = DiffModelAdmin.readonly_fields + ("name",)
    fields = ("name", "kind", "created_at", "updated_at")


class ArtifactLineageAdmin(DiffModelAdmin):
    list_display = (
        "artifact",
        "run",
        "is_input",
    )
    list_display_links = (
        "artifact",
        "run",
        "is_input",
    )
    readonly_fields = DiffModelAdmin.readonly_fields + ("artifact", "run")
    fields = ("artifact", "run", "is_input", "created_at", "updated_at")
