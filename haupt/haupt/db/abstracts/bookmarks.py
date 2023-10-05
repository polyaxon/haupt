from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from haupt.db.abstracts.diff import DiffModel


class BaseBookmark(DiffModel):
    enabled = models.BooleanField(default=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        abstract = True
        app_label = "db"
        db_table = "db_bookmark"
        verbose_name = "bookmark"
        verbose_name_plural = "bookmarks"

    def __str__(self) -> str:
        return "<{}-{}>".format(self.content_type, self.created_at)
