from django.db import models

from haupt.db.abstracts.diff import DiffModel
from haupt.db.abstracts.state import StateModel
from haupt.db.defs import Models
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
        app_label = "db"
        db_table = "db_artifact"


class BaseArtifactLineage(DiffModel):
    run = models.ForeignKey(
        Models.get_db_model_name("Run"),
        on_delete=models.CASCADE,
        related_name="artifacts_lineage",
    )
    artifact = models.ForeignKey(
        Models.get_db_model_name("Artifact"),
        on_delete=models.CASCADE,
        related_name="runs_lineage",
    )
    is_input = models.BooleanField(null=True, blank=True, default=False)

    class Meta:
        abstract = True
        app_label = "db"
        db_table = "db_artifactlineage"
        unique_together = (("run", "artifact", "is_input"),)
