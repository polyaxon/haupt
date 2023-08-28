from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from haupt.db.abstracts.diff import DiffModel


class StatsModel(DiffModel):
    user_stats = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )
    run_stats = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )
    model_stats = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )
    artifact_stats = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )
    component_stats = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )
    tracking_time_stats = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )

    class Meta:
        abstract = True
        app_label = "db"
