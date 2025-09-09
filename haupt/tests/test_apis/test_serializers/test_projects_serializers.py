import pytest

from haupt.apis.serializers.projects import (
    BookmarkedProjectSerializer,
    ProjectDetailSerializer,
    ProjectNameSerializer,
    ProjectSerializer,
)
from tests.base.case import BaseTestProjectSerializer


@pytest.mark.serializers_mark
class TestProjectNameSerializer(BaseTestProjectSerializer):
    serializer_class = ProjectNameSerializer
    expected_keys = {"name"}

    def test_serialize_one(self):
        obj1 = self.create_one()
        data = self.serializer_class(obj1).data

        assert set(data.keys()) == self.expected_keys
        for k, v in data.items():
            assert getattr(obj1, k) == v


@pytest.mark.serializers_mark
class TestProjectSerializer(BaseTestProjectSerializer):
    serializer_class = ProjectSerializer
    expected_keys = {
        "uuid",
        "name",
        "description",
        "tags",
        "user",
        "created_at",
        "updated_at",
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
class TestBookmarkedProjectSerializer(BaseTestProjectSerializer):
    serializer_class = BookmarkedProjectSerializer
    expected_keys = {
        "uuid",
        "name",
        "description",
        "tags",
        "user",
        "created_at",
        "updated_at",
        "bookmarked",
    }

    def create_one(self):
        return self.factory_class()

    def test_serialize_one(self):
        obj1 = self.create_one()
        data = self.serializer_class(obj1).data

        assert set(data.keys()) == self.expected_keys
        data.pop("created_at")
        data.pop("updated_at")
        assert data.pop("uuid") == obj1.uuid.hex
        assert data.pop("bookmarked") is False

        for k, v in data.items():
            assert getattr(obj1, k) == v


@pytest.mark.serializers_mark
class TestProjectDetailSerializer(TestProjectSerializer):
    serializer_class = ProjectDetailSerializer
    expected_keys = TestProjectSerializer.expected_keys | {
        "bookmarked",
        "readme",
        "live_state",
    }

    def test_serialize_one(self):
        obj1 = self.create_one()
        data = self.serializer_class(obj1).data

        assert set(data.keys()) == self.expected_keys
        data.pop("created_at")
        data.pop("updated_at")
        assert data.pop("uuid") == obj1.uuid.hex
        assert data.pop("bookmarked") is False

        for k, v in data.items():
            assert getattr(obj1, k) == v


del BaseTestProjectSerializer
