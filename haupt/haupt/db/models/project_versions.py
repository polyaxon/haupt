from haupt.db.abstracts.project_versions import BaseProjectVersion


class ProjectVersion(BaseProjectVersion):
    class Meta(BaseProjectVersion.Meta):
        app_label = "db"
        db_table = "db_projectversion"
