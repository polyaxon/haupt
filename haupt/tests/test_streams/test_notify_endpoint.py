#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import pytest

from asyncio import Future
from mock import patch

from polyaxon import settings
from polyaxon.api import STREAMS_V1_LOCATION
from polyaxon.connections import V1Connection, V1ConnectionKind, V1K8sResource
from polyaxon.lifecycle import V1StatusCondition, V1Statuses
from polyaxon.utils.test_utils import set_store
from tests.base.case import BaseTest


@pytest.mark.notifies_mark
class TestNotifyEndpoints(BaseTest):
    def setUp(self):
        super().setUp()
        self.store_root = set_store()
        settings.AGENT_CONFIG.connections = [
            V1Connection(
                name="slack",
                kind=V1ConnectionKind.SLACK,
                secret=V1K8sResource(name="some"),
            )
        ]

        self.base_url = STREAMS_V1_LOCATION + "namespace/owner/project/runs/uuid/notify"

    def test_notify_with_no_data(self):
        response = self.client.post(self.base_url, data={})
        assert response.status_code == 400

    def test_notify_with_no_condition(self):
        data = {"name": "test", "condition": None, "connections": ["test"]}
        response = self.client.post(self.base_url, data=data)
        assert response.status_code == 400

    def test_notify_with_no_notifications(self):
        data = {
            "name": "test",
            "condition": V1StatusCondition(
                type=V1Statuses.FAILED, status=True
            ).to_dict(),
            "connections": None,
        }
        response = self.client.post(self.base_url, data=data)
        assert response.status_code == 400

        data = {
            "name": "test",
            "condition": V1StatusCondition(
                type=V1Statuses.FAILED, status=True
            ).to_dict(),
            "connections": [],
        }
        response = self.client.post(self.base_url, data=data)
        assert response.status_code == 400

    def test_notify_with_no_agent_connections(self):
        settings.AGENT_CONFIG.connections = []
        data = {
            "name": "test",
            "condition": V1StatusCondition(
                type=V1Statuses.FAILED, status=True
            ).to_dict(),
            "connections": ["test1", "test2"],
        }
        response = self.client.post(self.base_url, data=data)
        assert response.status_code == 400

    def test_notify_with_non_recognized_connections(self):
        data = {
            "name": "test",
            "condition": V1StatusCondition(
                type=V1Statuses.FAILED, status=True
            ).to_dict(),
            "connections": ["test1", "test2"],
        }
        with patch(
            "polyaxon.agents.spawners.async_spawner.AsyncK8SManager"
        ) as manager_mock:
            manager_mock.return_value.setup.return_value = Future()
            manager_mock.return_value.setup.return_value.set_result(None)
            response = self.client.post(self.base_url, data=data)
            assert response.status_code == 200
