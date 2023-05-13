from django.db import models


class VisibilityModel(models.Model):
    is_public = models.BooleanField(
        default=False, help_text="If the entity is public or private."
    )

    class Meta:
        abstract = True
