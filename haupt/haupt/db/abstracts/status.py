from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from polyaxon.schemas import V1Statuses


class StatusModel(models.Model):
    status = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        db_index=True,
        default=V1Statuses.CREATED,
        choices=V1Statuses.to_choices(),
    )
    status_conditions = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )

    class Meta:
        abstract = True
