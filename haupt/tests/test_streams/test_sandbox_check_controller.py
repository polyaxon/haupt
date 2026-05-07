from unittest.mock import patch

import pytest

from rest_framework import status

from haupt.streams.controllers.sandbox_check import reverse_sandbox, sandbox_check
from polyaxon._env_vars.keys import ENV_KEYS_SECRET_INTERNAL_TOKEN
from polyaxon._sandbox.auth import derive_sandbox_token


pytestmark = pytest.mark.streams_mark


def test_sandbox_check_extracts_run_uuid():
    assert sandbox_check("/sandbox/v1/ns/owner/project/runs/uuid/ping") == "uuid"


def test_sandbox_check_accepts_nested_path_and_query_string():
    assert sandbox_check(
        "/sandbox/v1/ns/owner/project/runs/uuid/fs/read?path=/tmp/x&offset=1"
    ) == "uuid"
    assert sandbox_check("/sandbox/v1/ns/owner/project/runs/uuid/pty/id/ws") == "uuid"


@pytest.mark.parametrize(
    "uri",
    [
        "/services/v1/ns/owner/project/runs/uuid/ping",
        "/sandbox/v1/ns/owner/project",
        "/sandbox/v1/ns/owner/project/jobs/uuid/ping",
        "/sandbox/v1/ns/owner/project/runs/uuid",
        "/sandbox/v1/ns/owner/project/runs/uuid/",
    ],
)
def test_sandbox_check_rejects_invalid_sandbox_paths(uri):
    with pytest.raises(ValueError):
        sandbox_check(uri)


class TestReverseSandbox:
    def test_reverse_sandbox_returns_token_header(self):
        with patch.dict(
            "os.environ", {ENV_KEYS_SECRET_INTERNAL_TOKEN: "internal-token"}
        ):
            response = reverse_sandbox(run_uuid="uuid")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["SANDBOX_TOKEN"] == derive_sandbox_token(
            "internal-token", "uuid"
        )
        assert "SANDBOX_URI" not in response.headers
        assert "X-Polyaxon-Sandbox-Token" not in response.headers

    def test_reverse_sandbox_returns_500_when_internal_token_is_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            response = reverse_sandbox(run_uuid="uuid")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.content == b"Sandbox internal token not configured"
