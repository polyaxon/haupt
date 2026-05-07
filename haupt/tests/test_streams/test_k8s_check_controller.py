import asyncio

import pytest

from rest_framework import status

from haupt.streams.controllers.k8s_check import k8s_check, reverse_k8s
from polyaxon._k8s.manager.async_manager import AsyncK8sManager
from polyaxon._utils.test_utils import patch_settings


pytestmark = pytest.mark.streams_mark


@pytest.fixture(autouse=True)
def patch_client_settings():
    patch_settings(set_auth=False, set_client=True, set_cli=False, set_agent=False)


def test_k8s_check_extracts_exec_path_and_query_params():
    path, query_params = k8s_check(
        "/k8s/v1/ns/owner/project/runs/uuid/k8s_exec/pod/container"
        "?command=/bin/bash&stdin=true"
    )

    assert path == "api/v1/namespaces/ns/pods/pod/exec"
    assert query_params == "command=/bin/bash&stdin=true&container=container"


@pytest.mark.parametrize(
    "uri",
    [
        "/services/v1/ns/owner/project/runs/uuid/k8s_exec/pod/container",
        "/k8s/v1/ns/owner/project/runs/uuid/logs",
        "/k8s/v1/ns/owner/project/runs/uuid/k8s_exec/pod",
        "/k8s/v1/ns/owner/project/runs/uuid/k8s_exec/pod/container/extra",
    ],
)
def test_k8s_check_rejects_invalid_exec_paths(uri):
    with pytest.raises(ValueError):
        k8s_check(uri)


def test_reverse_k8s_rejects_empty_path():
    response = asyncio.run(reverse_k8s(path=""))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.content == b"A valid k8s path param is required"


def test_reverse_k8s_returns_upstream_and_token_headers(monkeypatch):
    class Config:
        host = "https://k8s.local"

    async def load_config(in_cluster):
        return Config()

    monkeypatch.setattr(AsyncK8sManager, "load_config", load_config)
    monkeypatch.setattr(
        AsyncK8sManager,
        "get_config_auth",
        lambda config: "k8s-token",
    )

    response = asyncio.run(reverse_k8s(path="api/v1/namespaces/ns/pods/pod/exec"))

    assert response.status_code == status.HTTP_200_OK
    assert (
        response.headers["K8S_URI"]
        == "https://k8s.local/api/v1/namespaces/ns/pods/pod/exec"
    )
    assert response.headers["K8S_TOKEN"] == "k8s-token"
