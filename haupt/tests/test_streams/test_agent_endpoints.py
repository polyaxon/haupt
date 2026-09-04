import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, Mock

from django.core.exceptions import BadRequest
from django.test import RequestFactory
from rest_framework import status

from clipped.utils.json import orjson_loads
from haupt.streams.endpoints import agents as agents_module


pytestmark = pytest.mark.streams_mark


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
