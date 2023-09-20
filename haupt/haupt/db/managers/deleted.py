from django.db import models

from polyaxon.schemas import LiveState


class LiveManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(live_state=LiveState.LIVE)


class ArchivedManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(live_state=LiveState.ARCHIVED)


class RestorableManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(live_state__in={LiveState.LIVE, LiveState.ARCHIVED})
