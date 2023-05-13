from django.db import models

from haupt.db.abstracts.describable import DescribableModel
from haupt.db.abstracts.diff import DiffModel
from haupt.db.abstracts.live_state import LiveStateModel
from haupt.db.abstracts.nameable import RequiredNameableModel
from haupt.db.abstracts.tag import TagModel
from haupt.db.abstracts.uid import UuidModel


class BaseCatalog(
    UuidModel,
    RequiredNameableModel,
    DiffModel,
    DescribableModel,
    TagModel,
):
    class Meta:
        abstract = True
        indexes = [models.Index(fields=["name"])]


class BaseLiveStateCatalog(
    BaseCatalog,
    LiveStateModel,
):
    class Meta:
        abstract = True
        indexes = [models.Index(fields=["name"])]
