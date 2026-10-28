import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, Mock
from uuid import UUID

from django.core.exceptions import BadRequest
from django.test import RequestFactory
from rest_framework import status

from clipped.utils.json import orjson_dumps, orjson_loads
from haupt.streams.endpoints import agents as agents_module
from polyaxon._env_vars.keys import ENV_KEYS_AGENT_INSTANCE


pytestmark = pytest.mark.streams_mark

AGENT_UUID = "8aac02e3a62a4f0d9b6a9b7e6d1c2f30"
OWN_INSTANCE = "foo.agents.{}".format(AGENT_UUID)


def run_collect_agent_data():
    return asyncio.run(
        agents_module.collect_agent_data(
            RequestFactory().post(
                "/internal/v1/polyaxon/default/foo/agents/uuid/collect"
            ),
            namespace="default",
            owner="foo",
            agent_uuid="uuid",
            methods=["POST"],
        )
    )


def test_collect_agent_data_returns_structured_artifacts_store_error(
    monkeypatch, caplog
):
    get_fs = AsyncMock(
        side_effect=PermissionError("private_key=super-secret token=other-secret")
    )
    get_fs_root_path = Mock()
    monkeypatch.setattr(agents_module, "validate_internal_auth", Mock())
    monkeypatch.setattr(agents_module.AppFS, "get_fs", get_fs)
    monkeypatch.setattr(
        agents_module.AppFS,
        "get_fs_root_path",
        get_fs_root_path,
    )
    caplog.set_level(logging.ERROR, logger="haupt.streams.agents")

    response = run_collect_agent_data()

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert orjson_loads(response.content) == {
        "errors": {
            "code": "artifacts_store_initialization_failed",
            "category": "storage",
            "message": "Could not initialize the configured artifacts store.",
            "exception": "PermissionError",
            "hints": [
                "Check the default artifacts store configuration and credentials "
                "available to the streams pod."
            ],
        }
    }
    get_fs.assert_awaited_once_with()
    get_fs_root_path.assert_not_called()
    assert "PermissionError" in caplog.text
    assert "Traceback (most recent call last):" in caplog.text
    assert "PermissionError: private_key=super-secret token=other-secret" in caplog.text
    assert "super-secret" not in response.content.decode()
    assert "other-secret" not in response.content.decode()


def test_collect_agent_data_preserves_internal_auth_failure(monkeypatch):
    get_fs = AsyncMock()
    monkeypatch.setattr(
        agents_module,
        "validate_internal_auth",
        Mock(side_effect=BadRequest("Request requires an authentication data.")),
    )
    monkeypatch.setattr(agents_module.AppFS, "get_fs", get_fs)

    response = run_collect_agent_data()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert orjson_loads(response.content) == {
        "errors": (
            "Request requires an authenticated internal service "
            "Request requires an authentication data."
        )
    }
    get_fs.assert_not_awaited()


@pytest.fixture
def k8s_manager_class(monkeypatch):
    manager_class = Mock(
        return_value=Mock(setup=AsyncMock(), delete_pods=AsyncMock(), close=AsyncMock())
    )
    monkeypatch.setattr(agents_module, "AsyncK8sManager", manager_class)
    return manager_class


def set_deployment(monkeypatch, namespace=None, agent_instance=None):
    monkeypatch.setattr(
        agents_module.settings,
        "CLIENT_CONFIG",
        Mock(namespace=namespace, in_cluster=False),
    )
    if agent_instance:
        monkeypatch.setenv(ENV_KEYS_AGENT_INSTANCE, agent_instance)
    else:
        monkeypatch.delenv(ENV_KEYS_AGENT_INSTANCE, raising=False)


def run_restart_agent_pod(namespace="ns", owner="foo", agent_uuid=AGENT_UUID):
    return asyncio.run(
        agents_module.restart_agent_pod(
            RequestFactory().post(
                "/streams/v1/{}/{}/agents/{}/k8s_restart".format(
                    namespace, owner, agent_uuid
                ),
                data=orjson_dumps({"service": "streams"}),
                content_type="application/json",
            ),
            namespace=namespace,
            owner=owner,
            agent_uuid=agent_uuid,
            methods=["POST"],
        )
    )


def test_restart_agent_pod_deletes_own_agent_services(monkeypatch, k8s_manager_class):
    # The deployed instance may use the dashed uuid form
    set_deployment(
        monkeypatch,
        namespace="ns",
        agent_instance="foo.agents.{}".format(UUID(AGENT_UUID)),
    )

    response = run_restart_agent_pod()

    assert response.status_code == status.HTTP_200_OK
    assert orjson_loads(response.content) == {"status": "scheduled"}
    k8s_manager_class.return_value.delete_pods.assert_awaited_once_with(
        namespace="ns", label_selector="app.kubernetes.io/name=ns-polyaxon-streams"
    )


@pytest.mark.parametrize(
    "agent_instance,namespace,owner,agent_uuid",
    [
        (OWN_INSTANCE, "other", "foo", AGENT_UUID),
        (OWN_INSTANCE, "ns", "bar", AGENT_UUID),
        (OWN_INSTANCE, "ns", "foo", "0" * 32),
        ("foo.bar", "ns", "foo", AGENT_UUID),
        ("foo.agents.not-a-uuid", "ns", "foo", AGENT_UUID),
    ],
)
def test_restart_agent_pod_rejects_other_agents(
    monkeypatch, k8s_manager_class, agent_instance, namespace, owner, agent_uuid
):
    set_deployment(monkeypatch, namespace="ns", agent_instance=agent_instance)

    response = run_restart_agent_pod(
        namespace=namespace, owner=owner, agent_uuid=agent_uuid
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    k8s_manager_class.assert_not_called()


def test_restart_agent_pod_without_deployment_config(monkeypatch, k8s_manager_class):
    set_deployment(monkeypatch)

    response = run_restart_agent_pod(namespace="other")

    assert response.status_code == status.HTTP_200_OK
    k8s_manager_class.return_value.delete_pods.assert_awaited_once_with(
        namespace="other",
        label_selector="app.kubernetes.io/name=other-polyaxon-streams",
    )


def test_restart_agent_pod_missing_target_is_scheduled(monkeypatch, k8s_manager_class):
    set_deployment(monkeypatch, namespace="ns", agent_instance=OWN_INSTANCE)
    k8s_manager_class.return_value.delete_pods.side_effect = Exception("not found")

    response = run_restart_agent_pod()

    assert response.status_code == status.HTTP_200_OK
    assert orjson_loads(response.content) == {"status": "scheduled"}
