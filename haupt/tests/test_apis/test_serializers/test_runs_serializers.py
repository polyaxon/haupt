#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import pytest

from haupt.apis.serializers.runs import RunDetailSerializer, RunStatusSerializer
from haupt.common import conf
from haupt.common.options.registry.k8s import K8S_NAMESPACE
from haupt.db.factories.runs import RunFactory
from haupt.db.managers.statuses import new_run_status, new_run_stop_status
from haupt.db.models.runs import Run
from polyaxon.lifecycle import V1StatusCondition, V1Statuses
from polyaxon.polyflow import V1CloningKind
from tests.base.case import BaseTestRunSerializer


@pytest.mark.serializers_mark
class TestRunDetailSerializer(BaseTestRunSerializer):
    model_class = Run
    factory_class = RunFactory
    query = Run.objects
    serializer_class = RunDetailSerializer
    expected_keys = {
        "uuid",
        "name",
        "project",
        "description",
        "created_at",
        "updated_at",
        "started_at",
        "finished_at",
        "wait_time",
        "duration",
        "status",
        "kind",
        "runtime",
        "meta_info",
        "pipeline",
        "original",
        "is_managed",
        "pending",
        "live_state",
        "tags",
        "inputs",
        "outputs",
        "settings",
        "readme",
        "content",
        "raw_content",
    }

    def create_one(self):
        return self.factory_class(project=self.project, user=self.user)

    def create_one_with_related(self):
        run = self.factory_class(project=self.project, user=self.user)
        run = self.factory_class(
            project=self.project,
            original=run,
            cloning_kind=V1CloningKind.CACHE,
            status=V1Statuses.RUNNING,
        )
        return run

    def test_serialize_one(self):
        obj1 = self.create_one_with_related()
        data = self.serializer_class(obj1).data

        assert set(data.keys()) == self.expected_keys
        assert data.pop("uuid") == obj1.uuid.hex
        assert data.pop("project") == obj1.project.name
        assert data.pop("original") == {
            "uuid": obj1.original.uuid.hex,
            "name": obj1.original.name,
            "kind": obj1.cloning_kind,
        }
        assert data.pop("settings") == {"namespace": conf.get(K8S_NAMESPACE)}
        data.pop("created_at")
        data.pop("updated_at")
        data.pop("started_at", None)
        data.pop("finished_at", None)

        for k, v in data.items():
            assert getattr(obj1, k) == v

        _ = self.serializer_class(obj1.original).data


@pytest.mark.serializers_mark
class TestRunStatusSerializer(TestRunDetailSerializer):
    serializer_class = RunStatusSerializer
    model_class = Run
    factory_class = RunFactory
    expected_keys = {"uuid", "status", "meta_info", "status_conditions"}

    def create_one(self):
        run = super().create_one()
        condition = V1StatusCondition.get_condition(
            type=V1Statuses.RUNNING,
            status="True",
            reason="Run is running",
            message="foo",
        )
        new_run_status(run, condition)
        new_run_stop_status(run, "stopping")
        return run

    def test_serialize_one(self):
        obj1 = self.create_one()
        data = self.serializer_class(obj1).data

        assert set(data.keys()) == self.expected_keys
        assert data.pop("uuid") == obj1.uuid.hex

        for k, v in data.items():
            assert getattr(obj1, k) == v

    def test_serialize_many(self):
        pass


del BaseTestRunSerializer
