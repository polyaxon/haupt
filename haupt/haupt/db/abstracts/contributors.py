from django.conf import settings
from django.db import models


class ContributorsModel(models.Model):
    contributors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="+"
    )

    class Meta:
        abstract = True
