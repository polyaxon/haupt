from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from polyaxon.schemas import V1Stages


class StageModel(models.Model):
    stage = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        db_index=True,
        default=V1Stages.TESTING,
        choices=V1Stages.to_choices(),
    )
    stage_conditions = models.JSONField(
        encoder=DjangoJSONEncoder, blank=True, null=True, default=dict
    )

    class Meta:
        abstract = True
