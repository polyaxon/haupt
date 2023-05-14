from haupt.db.abstracts.run_edges import BaseRunEdge


class RunEdge(BaseRunEdge):
    class Meta:
        app_label = "db"
        db_table = "db_runedge"
