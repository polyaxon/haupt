import pytest

from unittest.mock import AsyncMock, patch

from polyaxon import settings
from polyaxon._connections import V1Connection, V1ConnectionKind, V1ConnectionResource
from polyaxon._utils.test_utils import set_store
from polyaxon.api import STREAMS_V1_LOCATION
from polyaxon.schemas import V1StatusCondition, V1Statuses
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
                secret=V1ConnectionResource(name="some"),
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
            "polyaxon._k8s.executor.async_executor.AsyncK8sManager"
        ) as manager_mock:
            manager_mock.return_value.setup = AsyncMock(return_value=None)
            response = self.client.post(self.base_url, data=data)
            assert response.status_code == 200
