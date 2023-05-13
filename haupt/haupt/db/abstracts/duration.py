from django.db import models


class DurationModel(models.Model):
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    wait_time = models.IntegerField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)

    class Meta:
        abstract = True
