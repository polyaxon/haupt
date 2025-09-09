import pytest

from haupt.apis.serializers.project_versions import (
    ProjectVersionDetailSerializer,
    ProjectVersionSerializer,
)
from tests.base.case import BaseTestProjectVersionSerializer


@pytest.mark.serializers_mark
class TestProjectVersionSerializer(BaseTestProjectVersionSerializer):
    serializer_class = ProjectVersionSerializer
    expected_keys = {
        "uuid",
        "name",
        "description",
        "tags",
        "user",
        "created_at",
        "updated_at",
        "stage",
        "state",
        "kind",
    }

    def test_serialize_one(self):
        obj1 = self.create_one()
        data = self.serializer_class(obj1).data

        assert set(data.keys()) == self.expected_keys
        data.pop("created_at")
        data.pop("updated_at")
        assert data.pop("uuid") == obj1.uuid.hex

        for k, v in data.items():
            assert getattr(obj1, k) == v


@pytest.mark.serializers_mark
class TestProjectVersionDetailSerializer(TestProjectVersionSerializer):
    serializer_class = ProjectVersionDetailSerializer
    expected_keys = TestProjectVersionSerializer.expected_keys | {
        "owner",
        "project",
        "content",
        "readme",
        "run",
        "artifacts",
        "meta_info",
    }

    def test_serialize_one(self):
        obj1 = self.create_one()
        data = self.serializer_class(obj1).data

        assert set(data.keys()) == self.expected_keys
        data.pop("created_at")
        data.pop("updated_at")
        assert data.pop("uuid") == obj1.uuid.hex
        assert data.pop("owner") == obj1.project.owner.name
        assert data.pop("project") == obj1.project.name
        assert data.pop("artifacts") == []
        assert data.pop("meta_info") == {}

        for k, v in data.items():
            assert getattr(obj1, k) == v


del BaseTestProjectVersionSerializer
