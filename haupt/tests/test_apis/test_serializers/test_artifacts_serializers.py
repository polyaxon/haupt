import pytest
import random

from haupt.apis.serializers.artifacts import (
    RunArtifactLightSerializer,
    RunArtifactSerializer,
)
from haupt.common.test_cases.base import PolyaxonBaseTestSerializer
from haupt.db.factories.artifacts import ArtifactFactory
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.models.artifacts import Artifact, ArtifactLineage
from polyaxon.schemas import ManagedBy


@pytest.mark.serializers_mark
class TestArtifactSerializer(PolyaxonBaseTestSerializer):
    query = ArtifactLineage.objects
    factory_class = ArtifactFactory
    model_class = Artifact
    serializer_class = RunArtifactSerializer
    expected_keys = {
        "name",
        "kind",
        "path",
        "summary",
        "state",
        "is_input",
        "run",
        "meta_info",
    }

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()
        self.run = RunFactory(
            project=self.project,
            content="test",
            raw_content="test",
            managed_by=ManagedBy.AGENT,
        )
        self.state = self.project.owner.uuid

    def create_one(self):
        i = random.randint(1, 100)
        artifact = self.factory_class(name=f"name{i}", state=self.state)
        return ArtifactLineage.objects.create(artifact=artifact, run=self.run)

    def test_serialize_one(self):
        obj1 = self.create_one()
        data = self.serializer_class(self.query.get(id=obj1.id)).data

        assert set(data.keys()) == self.expected_keys

        assert data.pop("name") == obj1.artifact.name
        assert data.pop("path") == obj1.artifact.path
        assert data.pop("summary") == obj1.artifact.summary
        assert data.pop("state") == obj1.artifact.state.hex
        assert data.pop("run") == obj1.run.uuid.hex
        assert data.pop("kind") == obj1.artifact.kind
        assert data.pop("meta_info") == {
            "run": {"uuid": obj1.run.uuid.hex, "name": obj1.run.name}
        }
        for k, v in data.items():
            assert getattr(obj1, k) == v


@pytest.mark.serializers_mark
class TestArtifactLightSerializer(PolyaxonBaseTestSerializer):
    query = ArtifactLineage.objects
    factory_class = ArtifactFactory
    model_class = Artifact
    serializer_class = RunArtifactLightSerializer
    expected_keys = {"name", "kind", "is_input"}

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()
        self.run = RunFactory(
            project=self.project,
            content="test",
            raw_content="test",
            managed_by=ManagedBy.AGENT,
        )
        self.state = self.project.owner.uuid

    def create_one(self):
        i = random.randint(1, 100)
        artifact = self.factory_class(name=f"name{i}", state=self.state)
        return ArtifactLineage.objects.create(artifact=artifact, run=self.run)

    def test_serialize_one(self):
        obj1 = self.create_one()
        data = self.serializer_class(self.query.get(id=obj1.id)).data

        assert set(data.keys()) == self.expected_keys

        assert data.pop("name") == obj1.artifact.name
        assert data.pop("kind") == obj1.artifact.kind
        for k, v in data.items():
            assert getattr(obj1, k) == v


del PolyaxonBaseTestSerializer
