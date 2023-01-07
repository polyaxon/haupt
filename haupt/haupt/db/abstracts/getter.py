#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_db_model_name(name: str) -> str:
    db = settings.AUTH_USER_MODEL.split(".")[0]
    return "{}.{}".format(db, name)


def get_db_model(name: str) -> str:
    model_name = get_db_model_name(name)
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


def get_project_model():
    return get_db_model("Project")


def get_run_model():
    return get_db_model("Run")


def get_artifact_model():
    return get_db_model("Artifact")


def get_lineage_model():
    return get_db_model("ArtifactLineage")
