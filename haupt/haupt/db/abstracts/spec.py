from django.db import models


class SpecModel(models.Model):
    raw_content = models.TextField(
        null=True,
        blank=True,
        help_text="The raw yaml content of the polyaxonfile/specification.",
    )
    content = models.TextField(
        null=True,
        blank=True,
        help_text="The compiled yaml content of the polyaxonfile/specification.",
    )

    class Meta:
        abstract = True
