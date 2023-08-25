from django.db import models

from haupt.db.abstracts.stats import StatsModel


class ProjectStats(StatsModel):
    project = models.ForeignKey(
        "db.Project", on_delete=models.CASCADE, related_name="stats"
    )

    class Meta(StatsModel.Meta):
        app_label = "db"
        db_table = "db_projectstats"
