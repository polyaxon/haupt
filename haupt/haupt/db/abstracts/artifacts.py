#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.db import models

from haupt.db.abstracts.diff import DiffModel
from haupt.db.abstracts.getter import get_db_model_name
from haupt.db.abstracts.state import StateModel
from traceml.artifacts import V1ArtifactKind


class BaseArtifact(DiffModel, StateModel):
    name = models.CharField(max_length=256, db_index=True)
    kind = models.CharField(
        max_length=12,
        db_index=True,
        choices=V1ArtifactKind.to_choices(),
    )
    path = models.CharField(max_length=256, blank=True, null=True)
    summary = models.JSONField()

    class Meta:
        abstract = True


class BaseArtifactLineage(DiffModel):
    run = models.ForeignKey(
        get_db_model_name("Run"),
        on_delete=models.CASCADE,
        related_name="artifacts_lineage",
    )
    artifact = models.ForeignKey(
        get_db_model_name("Artifact"),
        on_delete=models.CASCADE,
        related_name="runs_lineage",
    )
    is_input = models.BooleanField(null=True, blank=True, default=False)

    class Meta:
        abstract = True
