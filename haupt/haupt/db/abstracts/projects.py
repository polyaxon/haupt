import uuid

from django.core.validators import validate_slug
from django.db import models

from haupt.common.validation.blacklist import validate_blacklist_name
from haupt.db.abstracts.catalogs import BaseLiveStateCatalog
from haupt.db.abstracts.readme import ReadmeModel
from polyaxon.constants.globals import DEFAULT


class Owner:
    name = DEFAULT
    uuid = uuid.UUID("9b0a3806e3f84ea1959a7842e34129ed")
    id = 1


class Actor:
    username = DEFAULT
    id = 1


class BaseProject(BaseLiveStateCatalog, ReadmeModel):
    name = models.CharField(
        max_length=128, validators=[validate_slug, validate_blacklist_name], unique=True
    )

    class Meta(BaseLiveStateCatalog.Meta):
        abstract = True

    @property
    def owner(self):
        return Owner

    @property
    def owner_id(self):
        return Owner.id

    @property
    def actor(self):
        return Actor
