from django.core.validators import validate_slug
from django.db import models

from haupt.db.abstracts.contributors import ContributorsModel
from haupt.db.abstracts.diff import DiffModel
from haupt.db.abstracts.duration import DurationModel
from haupt.db.abstracts.nameable import NameableModel
from haupt.db.abstracts.status import StatusModel
from haupt.db.abstracts.tag import TagModel
from haupt.db.abstracts.uid import UuidModel
from haupt.db.defs import Models


class BaseEvent(
    UuidModel,
    DiffModel,
    DurationModel,
    NameableModel,
    StatusModel,
    TagModel,
    ContributorsModel,
):
    name = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        default=None,
        validators=[validate_slug],
    )
    version = models.ForeignKey(
        "db.ProjectVersion", on_delete=models.CASCADE, related_name="events"
    )
    session = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        default=None,
        db_index=True,
        validators=[validate_slug],
    )
    user = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        default=None,
        db_index=True,
        validators=[validate_slug],
    )
    project = models.ForeignKey(
        Models.get_db_model_name("Project"),
        on_delete=models.CASCADE,
        related_name="runs",
    )
    meta_info = models.JSONField(null=True, blank=True, default=dict)
    inputs = models.JSONField(null=True, blank=True)
    outputs = models.JSONField(null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True
        app_label = "db"
        db_table = "db_event"
        indexes = [models.Index(fields=["name"])]
