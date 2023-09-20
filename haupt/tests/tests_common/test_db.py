import sqlite3
import uuid

from typing import List, Union

from clipped.utils.json import orjson_dumps
from clipped.utils.versions import compare_versions

from django.conf import settings
from django.test import TestCase
from django.utils.timezone import now

from haupt.common.db import RawBulkInserter, RawBulkUpdater
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.users import UserFactory
from haupt.db.models.runs import Run
from polyaxon.schemas import ManagedBy, V1RunKind

_RUN_MODEL_FIELDS = (
    "uuid",
    "name",
    "created_at",
    "updated_at",
    "description",
    "tags",
    "kind",
    "managed_by",
    "pending",
    "live_state",
    "content",
    "project_id",
    "user_id",
)


_RUN_MODEL_UPDATE_FIELDS = (
    "name",
    "updated_at",
    "description",
    "tags",
)


def _get_tags(values: List[str]) -> Union[List[str], str]:
    if settings.DB_ENGINE_NAME == "sqlite":
        return orjson_dumps({v: "" for v in values})
    return values


class TestRawBulkInserter(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()
        self.date_value = now()

    def test_insert_less_than_chunk_size(self):
        runs_count = Run.objects.count()
        inserter = RawBulkInserter(Run, _RUN_MODEL_FIELDS)
        inserter.queue_row(
            uuid.uuid4().hex,
            "Foo",
            self.date_value,
            self.date_value,
            "foo desc",
            _get_tags(["foo", "bar"]),
            V1RunKind.JOB,
            ManagedBy.AGENT,
            True,
            1,
            "foo content",
            self.project.id,
            self.user.id,
        )
        inserter.queue_row(
            uuid.uuid4().hex,
            "Bar",
            self.date_value,
            self.date_value,
            "bar desc",
            _get_tags(["foo", "moo"]),
            V1RunKind.SERVICE,
            ManagedBy.AGENT,
            True,
            1,
            "bar content",
            self.project.id,
            self.user.id,
        )

        assert Run.objects.count() == runs_count
        inserter.insert()
        assert Run.objects.count() == runs_count + 2
        assert Run.objects.filter(name="Foo").count() == 1
        assert Run.objects.filter(kind=V1RunKind.JOB).count() == 1
        assert Run.objects.filter(name="Bar").count() == 1
        assert Run.objects.filter(kind=V1RunKind.SERVICE).count() == 1
        if settings.DB_ENGINE_NAME == "sqlite":
            assert Run.objects.filter(tags__has_key=["foo"]).count() == 2
            assert Run.objects.filter(tags__has_key=["bar"]).count() == 1
        else:
            assert Run.objects.filter(tags__contains=["foo"]).count() == 2
            assert Run.objects.filter(tags__contains=["bar"]).count() == 1

    def test_insert_more_than_chunk_size(self):
        runs_count = Run.objects.count()
        inserter = RawBulkInserter(Run, _RUN_MODEL_FIELDS, chunk_size=1)
        inserter.queue_row(
            uuid.uuid4().hex,
            "Foo",
            self.date_value,
            self.date_value,
            "foo desc",
            _get_tags(["foo", "bar"]),
            V1RunKind.JOB,
            ManagedBy.AGENT,
            True,
            1,
            "foo content",
            self.project.id,
            self.user.id,
        )
        assert Run.objects.count() == runs_count + 1
        inserter.queue_row(
            uuid.uuid4().hex,
            "Bar",
            self.date_value,
            self.date_value,
            "bar desc",
            _get_tags(["foo", "moo"]),
            V1RunKind.SERVICE,
            ManagedBy.AGENT,
            True,
            1,
            "bar content",
            self.project.id,
            self.user.id,
        )
        assert Run.objects.count() == runs_count + 2

        assert Run.objects.filter(name="Foo").count() == 1
        assert Run.objects.filter(kind=V1RunKind.JOB).count() == 1
        assert Run.objects.filter(name="Bar").count() == 1
        assert Run.objects.filter(kind=V1RunKind.SERVICE).count() == 1
        if settings.DB_ENGINE_NAME == "sqlite":
            assert Run.objects.filter(tags__has_key=["foo"]).count() == 2
            assert Run.objects.filter(tags__has_key=["bar"]).count() == 1
        else:
            assert Run.objects.filter(tags__contains=["foo"]).count() == 2
            assert Run.objects.filter(tags__contains=["bar"]).count() == 1

    def test_fetch_ids_True(self):
        inserter = RawBulkInserter(Run, _RUN_MODEL_FIELDS, fetch_ids=True)
        inserter.queue_row(
            uuid.uuid4().hex,
            "Foo",
            self.date_value,
            self.date_value,
            "foo desc",
            _get_tags(["foo", "bar"]),
            V1RunKind.JOB,
            ManagedBy.AGENT,
            True,
            1,
            "foo content",
            self.project.id,
            self.user.id,
        )
        inserter.queue_row(
            uuid.uuid4().hex,
            "Bar",
            self.date_value,
            self.date_value,
            "bar desc",
            _get_tags(["foo", "moo"]),
            V1RunKind.SERVICE,
            ManagedBy.AGENT,
            True,
            1,
            "bar content",
            self.project.id,
            self.user.id,
        )
        inserter.insert()

        ids = inserter.all_created_ids
        assert (
            Run.objects.filter(
                id=ids[0],
                name="Foo",
                kind=V1RunKind.JOB,
                project_id=self.project.id,
                user_id=self.user.id,
            ).count()
            == 1
        )
        assert (
            Run.objects.filter(
                id=ids[1],
                name="Bar",
                kind=V1RunKind.SERVICE,
                project_id=self.project.id,
                user_id=self.user.id,
            ).count()
            == 1
        )


class TestRawBulkUpdater(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()
        self.date_value = now()
        self.runs_count = Run.objects.count()
        inserter = RawBulkInserter(Run, _RUN_MODEL_FIELDS, fetch_ids=True)
        inserter.queue_row(
            uuid.uuid4().hex,
            "Foo",
            self.date_value,
            self.date_value,
            "foo desc",
            _get_tags(["foo", "bar"]),
            V1RunKind.JOB,
            ManagedBy.AGENT,
            True,
            1,
            "foo content",
            self.project.id,
            self.user.id,
        )
        inserter.queue_row(
            uuid.uuid4().hex,
            "Bar",
            self.date_value,
            self.date_value,
            "bar desc",
            _get_tags(["foo", "bar"]),
            V1RunKind.SERVICE,
            ManagedBy.AGENT,
            True,
            1,
            "bar content",
            self.project.id,
            self.user.id,
        )
        inserter.insert()

        assert Run.objects.count() == self.runs_count + 2

        run1 = Run.objects.filter(
            name="Foo", kind=V1RunKind.JOB, project_id=self.project.id
        )
        assert run1.count() == 1
        self.run1 = run1[0]

        run2 = Run.objects.filter(
            name="Bar", kind=V1RunKind.SERVICE, project_id=self.project.id
        )
        assert run2.count() == 1
        self.run2 = run2[0]
        self.date_value2 = now()
        assert self.date_value != self.date_value2

    def test_update_less_than_chunk_size(self):
        if settings.DB_ENGINE_NAME == "sqlite":
            with self.assertRaises(ValueError):
                RawBulkUpdater(Run, ("id",), _RUN_MODEL_UPDATE_FIELDS, chunk_size=1)
            return

        updater = RawBulkUpdater(Run, ("id",), _RUN_MODEL_UPDATE_FIELDS)
        updater.queue_row(
            (self.run1.id,), ("FooBar", self.date_value2, "new desc", ["new", "tag1"])
        )
        updater.queue_row(
            (self.run2.id,), ("FooBar", self.date_value2, "new desc", ["new", "tag2"])
        )
        updater.update()

        assert Run.objects.count() == self.runs_count + 2
        run1 = Run.objects.get(id=self.run1.id)
        assert run1.name == "FooBar"
        assert run1.kind == V1RunKind.JOB
        assert run1.managed_by == ManagedBy.AGENT
        assert run1.description == "new desc"
        assert run1.tags == ["new", "tag1"]
        assert run1.created_at == self.date_value
        assert run1.updated_at == self.date_value2
        run2 = Run.objects.get(id=self.run2.id)
        assert run2.name == "FooBar"
        assert run2.kind == V1RunKind.SERVICE
        assert run2.managed_by == ManagedBy.AGENT
        assert run2.description == "new desc"
        assert run2.tags == ["new", "tag2"]
        assert run2.created_at == self.date_value
        assert run2.updated_at == self.date_value2
        assert Run.objects.filter(tags__contains=["new"]).count() == 2
        assert Run.objects.filter(tags__contains=["tag1"]).count() == 1

    def test_update_more_than_chunk_size(self):
        if settings.DB_ENGINE_NAME == "sqlite":
            with self.assertRaises(ValueError):
                RawBulkUpdater(Run, ("id",), _RUN_MODEL_UPDATE_FIELDS, chunk_size=1)
            return

        updater = RawBulkUpdater(Run, ("id",), _RUN_MODEL_UPDATE_FIELDS, chunk_size=1)
        updater.queue_row(
            (self.run1.id,), ("FooBar", self.date_value2, "new desc", ["new", "tag1"])
        )
        run1 = Run.objects.get(id=self.run1.id)
        assert run1.name == "FooBar"
        assert run1.kind == V1RunKind.JOB
        assert run1.managed_by == ManagedBy.AGENT
        assert run1.description == "new desc"
        assert run1.tags == ["new", "tag1"]
        assert run1.created_at == self.date_value
        assert run1.updated_at == self.date_value2
        assert Run.objects.filter(tags__contains=["new"]).count() == 1
        assert Run.objects.filter(tags__contains=["tag1"]).count() == 1
        assert Run.objects.filter(tags__contains=["tag2"]).count() == 0

        updater.queue_row(
            (self.run2.id,), ("FooBar", self.date_value2, "new desc", ["new", "tag2"])
        )
        run2 = Run.objects.get(id=self.run2.id)
        assert run2.name == "FooBar"
        assert run2.kind == V1RunKind.SERVICE
        assert run2.managed_by == ManagedBy.AGENT
        assert run2.tags == ["new", "tag2"]
        assert run2.created_at == self.date_value
        assert run2.updated_at == self.date_value2
        assert Run.objects.filter(tags__contains=["new"]).count() == 2
        assert Run.objects.filter(tags__contains=["tag1"]).count() == 1
        assert Run.objects.filter(tags__contains=["tag2"]).count() == 1


if settings.DB_ENGINE_NAME == "sqlite" and compare_versions(
    sqlite3.sqlite_version, "3.30.0", "<"
):
    del TestRawBulkInserter
    del TestRawBulkUpdater
