from typing import Type

from clipped.decorators.cached_property import cached_property

from django.apps import apps as django_apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db import models


class _Models:
    @staticmethod
    def get_db_model_name(name: str) -> str:
        db = settings.AUTH_USER_MODEL.split(".")[0]
        return "{}.{}".format(db, name)

    @classmethod
    def get_db_model(cls, name: str) -> Type[models.Model]:
        model_name = cls.get_db_model_name(name)
        try:
            return django_apps.get_model(model_name, require_ready=False)
        except ValueError:
            raise ImproperlyConfigured(
                "{} must be of the form 'app_label.model_name'".format(model_name)
            )
        except LookupError:
            raise ImproperlyConfigured(
                "{} refers to model '{}' that has not been installed".format(
                    name, model_name
                )
            )

    @cached_property
    def User(self) -> Type[models.Model]:
        return get_user_model()

    @cached_property
    def Project(self) -> Type[models.Model]:
        return self.get_db_model("Project")

    @cached_property
    def Run(self) -> Type[models.Model]:
        return self.get_db_model("Run")

    @cached_property
    def Artifact(self) -> Type[models.Model]:
        return self.get_db_model("Artifact")

    @cached_property
    def ArtifactLineage(self) -> Type[models.Model]:
        return self.get_db_model("ArtifactLineage")

    @cached_property
    def RunEdge(self) -> Type[models.Model]:
        return self.get_db_model("RunEdge")

    @cached_property
    def ProjectVersion(self) -> Type[models.Model]:
        return self.get_db_model("ProjectVersion")

    @cached_property
    def ProjectStats(self) -> Type[models.Model]:
        return self.get_db_model("ProjectStats")

    @cached_property
    def Bookmark(self) -> Type[models.Model]:
        return self.get_db_model("Bookmark")


Models = _Models()
