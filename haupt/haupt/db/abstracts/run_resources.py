from django.db import models


class RunResources(models.Model):
    memory = models.FloatField(blank=True, null=True, default=0)
    cpu = models.FloatField(blank=True, null=True, default=0)
    gpu = models.FloatField(blank=True, null=True, default=0)
    custom = models.FloatField(blank=True, null=True, default=0)
    cost = models.FloatField(blank=True, null=True, default=0)

    class Meta:
        abstract = True
