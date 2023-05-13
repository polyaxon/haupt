import uuid

from django.db import models


class UuidModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=False)

    class Meta:
        abstract = True
