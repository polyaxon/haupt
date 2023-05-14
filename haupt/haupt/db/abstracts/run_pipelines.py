from django.db import models
from django.utils.timezone import now


class RunPipelines(models.Model):
    pipeline = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="pipeline_runs",
    )
    controller = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="controller_runs",
    )
    upstream_runs = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        through="db.RunEdge",
        related_name="downstream_runs",
    )
    schedule_at = models.DateTimeField(blank=True, null=True, db_index=True)
    checked_at = models.DateTimeField(blank=True, null=True, default=now, db_index=True)

    class Meta:
        abstract = True
