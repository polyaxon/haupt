from haupt.db.abstracts.artifacts import BaseArtifact, BaseArtifactLineage


class Artifact(BaseArtifact):
    class Meta(BaseArtifact.Meta):
        unique_together = (("name", "state"),)


class ArtifactLineage(BaseArtifactLineage):
    pass
