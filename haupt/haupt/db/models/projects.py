from haupt.db.abstracts.projects import BaseProject


class Project(BaseProject):
    class Meta(BaseProject.Meta):
        app_label = "db"
        db_table = "db_project"
