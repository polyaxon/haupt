from django.db import models


class ColorModel(models.Model):
    color = models.CharField(max_length=6, blank=True, null=True)

    class Meta:
        abstract = True
