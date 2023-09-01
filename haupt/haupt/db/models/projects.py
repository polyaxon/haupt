from django.core.validators import validate_slug
from django.db import models

from haupt.common.validation.blacklist import validate_blacklist_name
from haupt.db.abstracts.catalogs import BaseLiveStateCatalog
from haupt.db.abstracts.contributors import ContributorsModel
from haupt.db.abstracts.projects import Actor, Owner
from haupt.db.abstracts.readme import ReadmeModel


class Project(BaseLiveStateCatalog, ReadmeModel, ContributorsModel):
    latest_stats = models.OneToOneField(
        "db.ProjectStats",
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=128, validators=[validate_slug, validate_blacklist_name], unique=True
    )

    class Meta(BaseLiveStateCatalog.Meta):
        app_label = "db"
        db_table = "db_project"

    @property
    def owner(self):
        return Owner

    @property
    def owner_id(self):
        return Owner.id

    @property
    def actor(self):
        return Actor
