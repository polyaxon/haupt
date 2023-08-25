from django.db import models

from haupt.db.abstracts.diff import DiffModel


class StatsModel(DiffModel):
    user_count = models.IntegerField(null=True, blank=True, default=0)
    run_count = models.IntegerField(null=True, blank=True, default=0)
    model_count = models.IntegerField(null=True, blank=True, default=0)
    artifact_count = models.IntegerField(null=True, blank=True, default=0)
    component_count = models.IntegerField(null=True, blank=True, default=0)
    tracking_time = models.IntegerField(null=True, blank=True, default=0)

    class Meta:
        abstract = True
        app_label = "db"
