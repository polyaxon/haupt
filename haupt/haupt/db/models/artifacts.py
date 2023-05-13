from haupt.db.abstracts.artifacts import BaseArtifact, BaseArtifactLineage


class Artifact(BaseArtifact):
    class Meta:
        app_label = "db"
        unique_together = (("name", "state"),)
        db_table = "db_artifact"


class ArtifactLineage(BaseArtifactLineage):
    class Meta:
        app_label = "db"
        unique_together = (("run", "artifact", "is_input"),)
        db_table = "db_artifactlineage"
