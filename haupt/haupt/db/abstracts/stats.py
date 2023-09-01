from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from haupt.db.abstracts.diff import DiffModel


class StatsModel(DiffModel):
    created_at = models.DateTimeField(db_index=True)
    user = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )
    run = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )
    status = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )
    version = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )
    tracking_time = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )

    class Meta:
        abstract = True
        app_label = "db"
