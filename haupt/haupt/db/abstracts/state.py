from django.db import models


class StateModel(models.Model):
    state = models.UUIDField(db_index=True)

    class Meta:
        abstract = True


class OptionalStateModel(models.Model):
    state = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True
