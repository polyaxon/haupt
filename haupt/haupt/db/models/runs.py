from haupt.db.abstracts.runs import BaseRun


class Run(BaseRun):
    class Meta(BaseRun.Meta):
        app_label = "db"
        db_table = "db_run"
