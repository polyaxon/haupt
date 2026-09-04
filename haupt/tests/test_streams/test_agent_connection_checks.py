import asyncio
import logging
import pytest
from unittest.mock import AsyncMock

from django.test import RequestFactory
from rest_framework import status

from clipped.utils.json import orjson_loads
from haupt.streams.connections.fs import AppFS
from haupt.streams.controllers import connection_check
from haupt.streams.endpoints import agents as agents_module
from polyaxon import settings
from polyaxon._connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
    V1ConnectionResource,
    V1HostPathConnection,
)
from polyaxon._env_vars.keys import ENV_KEYS_ARTIFACTS_STORE_NAME
from polyaxon._schemas.agent import AgentConfig
from polyaxon._utils.test_utils import patch_settings
from polyaxon.settings import set_agent_config


pytestmark = pytest.mark.streams_mark


class FakeFS:
    async_impl = True

    def __init__(self):
        self.files = {}
        self.operations = []
        self.cat_error = None

    async def _pipe(self, path, value):
        self.operations.append(("pipe", path))
        self.files[path] = value

    async def _cat(self, path):
        self.operations.append(("cat", path))
        if self.cat_error:
            raise self.cat_error
        return self.files[path]

    async def _rm(self, path, recursive=False):
        self.operations.append(("rm", path))
        self.files.pop(path, None)


@pytest.fixture(autouse=True)
def patch_agent_settings(tmp_path, monkeypatch):
    patch_settings(set_auth=False, set_client=True, set_cli=False, set_agent=False)
    settings.CLIENT_CONFIG.archives_root = str(tmp_path / "archives")
    settings.CLIENT_CONFIG.in_cluster = True
    monkeypatch.delenv(ENV_KEYS_ARTIFACTS_STORE_NAME, raising=False)
    AppFS._connections = {}
    AppFS._refresh_state = {}
    set_agent_config(
        AgentConfig(
            namespace="default",
            artifacts_store=V1Connection(
                name="default-artifacts",
                kind=V1ConnectionKind.HOST_PATH,
                schema_=V1HostPathConnection(
                    host_path=str(tmp_path / "artifacts"),
                    mount_path=str(tmp_path / "artifacts"),
                ),
            ),
            connections=[],
        )
    )


@pytest.fixture(autouse=True)
def fake_kubernetes(monkeypatch):
    managers = []

    class FakeK8sManager:
        def __init__(self, namespace, in_cluster):
            self.closed = False
            self.list_pods_call = None
            managers.append(self)

        async def setup(self):
            pass

        async def list_pods(self, namespace, reraise=True, limit=1):
            self.list_pods_call = {
                "namespace": namespace,
                "reraise": reraise,
                "limit": limit,
            }

        async def close(self):
            self.closed = True

    monkeypatch.setattr(connection_check, "AsyncK8sManager", FakeK8sManager)
    return managers


def make_bucket_connection(kind):
    return V1Connection(
        name="default-artifacts",
        kind=kind,
        schema_=V1BucketConnection(bucket="{}://bucket".format(kind.value)),
        secret=V1ConnectionResource(name="artifacts-secret"),
    )


def set_default_artifacts_store(connection):
    set_agent_config(
        AgentConfig(
            namespace="default",
            artifacts_store=connection,
            connections=[],
        )
    )


def patch_fs(monkeypatch, fs, store_path):
    async def get_fs(connection=None):
        assert connection == "default-artifacts"
        return fs

    def get_fs_root_path(connection=None):
        assert connection == "default-artifacts"
        return store_path

    monkeypatch.setattr(connection_check.AppFS, "get_fs", get_fs)
    monkeypatch.setattr(connection_check.AppFS, "get_fs_root_path", get_fs_root_path)


def run_default_check():
    return asyncio.run(
        connection_check.check_default_agent_connections(
            namespace="default",
            agent_uuid="uuid",
        )
    )


def test_check_agent_connection_endpoint_uses_streams_auth_model(monkeypatch):
    expected_data = {"status": "passed", "results": []}
    default_check = AsyncMock(return_value=expected_data)
    named_check = AsyncMock()

    def fail_internal_auth(request):
        raise AssertionError("streams endpoint must not validate internal auth")

    monkeypatch.setattr(agents_module, "check_default_agent_connections", default_check)
    monkeypatch.setattr(agents_module, "check_named_agent_connection", named_check)
    monkeypatch.setattr(agents_module, "validate_internal_auth", fail_internal_auth)

    response = asyncio.run(
        agents_module.check_agent_connection(
            RequestFactory().post(
                "/streams/v1/default/foo/agents/uuid/connections_check",
                data={},
                content_type="application/json",
            ),
            namespace="default",
            owner="foo",
            agent_uuid="uuid",
            methods=["POST"],
        )
    )

    assert response.status_code == status.HTTP_200_OK
    assert orjson_loads(response.content) == expected_data
    default_check.assert_awaited_once_with(namespace="default", agent_uuid="uuid")
    named_check.assert_not_awaited()


def test_check_agent_connection_endpoint_preserves_connection_contract(monkeypatch):
    expected_data = {"status": "failed", "results": []}
    named_check = AsyncMock(return_value=expected_data)
    default_check = AsyncMock()

    monkeypatch.setattr(agents_module, "check_named_agent_connection", named_check)
    monkeypatch.setattr(agents_module, "check_default_agent_connections", default_check)
    response = asyncio.run(
        agents_module.check_agent_connection(
            RequestFactory().post(
                "/streams/v1/default/foo/agents/uuid/connections_check",
                data={"connection": "repo"},
                content_type="application/json",
            ),
            namespace="default",
            owner="foo",
            agent_uuid="uuid",
            methods=["POST"],
        )
    )

    assert response.status_code == status.HTTP_200_OK
    assert orjson_loads(response.content) == expected_data
    named_check.assert_awaited_once_with(connection_name="repo")
    default_check.assert_not_awaited()


def test_check_default_artifacts_store_success(monkeypatch, fake_kubernetes):
    fs = FakeFS()
    set_default_artifacts_store(make_bucket_connection(V1ConnectionKind.GCS))
    patch_fs(monkeypatch, fs, "gs://bucket")

    data = run_default_check()

    assert data["status"] == "passed"
    assert [result["connection"]["name"] for result in data["results"]] == [
        "default-artifacts",
        "agent_kubernetes",
    ]
    assert data["results"][0]["connection"] == {
        "name": "default-artifacts",
        "kind": "gcs",
        "configured_sources": ["schema", "secret"],
    }
    assert [check["name"] for check in data["results"][0]["checks"]] == ["access"]
    assert [operation for operation, _ in fs.operations] == ["pipe", "cat", "rm"]
    assert fs.files == {}
    assert fake_kubernetes[0].list_pods_call == {
        "namespace": "default",
        "reraise": True,
        "limit": 1,
    }
    assert fake_kubernetes[0].closed is True


def test_check_default_s3_artifacts_store(monkeypatch):
    fs = FakeFS()
    set_default_artifacts_store(make_bucket_connection(V1ConnectionKind.S3))
    patch_fs(monkeypatch, fs, "s3://bucket")

    data = run_default_check()

    assert data["status"] == "passed"
    assert data["results"][0]["connection"]["kind"] == "s3"
    assert [operation for operation, _ in fs.operations] == ["pipe", "cat", "rm"]


def test_check_default_wasb_artifacts_store(monkeypatch):
    fs = FakeFS()
    set_default_artifacts_store(make_bucket_connection(V1ConnectionKind.WASB))
    patch_fs(monkeypatch, fs, "wasbs://bucket")

    data = run_default_check()

    assert data["status"] == "passed"
    assert data["results"][0]["connection"]["kind"] == "wasb"
    assert [operation for operation, _ in fs.operations] == ["pipe", "cat", "rm"]


def test_check_host_path_requires_existing_root(tmp_path, monkeypatch):
    fs = FakeFS()
    missing_root = tmp_path / "missing-root"
    connection = V1Connection(
        name="default-artifacts",
        kind=V1ConnectionKind.HOST_PATH,
        schema_=V1HostPathConnection(
            host_path=str(missing_root), mount_path=str(missing_root)
        ),
    )
    set_default_artifacts_store(connection)
    patch_fs(monkeypatch, fs, str(missing_root))

    data = run_default_check()

    assert data["status"] == "failed"
    assert data["results"][0]["checks"][0]["code"] == "connection_mount_path_missing"
    assert not missing_root.exists()
    assert fs.operations == []


def test_check_host_path_requires_mount_point(tmp_path, monkeypatch):
    fs = FakeFS()
    existing_root = tmp_path / "existing-root"
    existing_root.mkdir()
    connection = V1Connection(
        name="default-artifacts",
        kind=V1ConnectionKind.HOST_PATH,
        schema_=V1HostPathConnection(
            host_path=str(existing_root), mount_path=str(existing_root)
        ),
    )
    set_default_artifacts_store(connection)
    patch_fs(monkeypatch, fs, str(existing_root))
    monkeypatch.setattr(connection_check, "_read_mount_points", lambda: [])

    data = run_default_check()

    assert data["status"] == "failed"
    assert data["results"][0]["checks"][0]["code"] == (
        "connection_mount_path_not_mounted"
    )
    assert fs.operations == []


def test_check_volume_claim_requires_existing_root(tmp_path, monkeypatch):
    fs = FakeFS()
    missing_root = tmp_path / "missing-root"
    connection = V1Connection(
        name="default-artifacts",
        kind=V1ConnectionKind.VOLUME_CLAIM,
        schema_=V1ClaimConnection(volume_claim="claim", mount_path=str(missing_root)),
    )
    set_default_artifacts_store(connection)
    patch_fs(monkeypatch, fs, str(missing_root))

    data = run_default_check()

    assert data["status"] == "failed"
    assert data["results"][0]["checks"][0]["code"] == "connection_mount_path_missing"
    assert not missing_root.exists()
    assert fs.operations == []


def test_check_volume_claim_requires_mount_point(tmp_path, monkeypatch):
    fs = FakeFS()
    existing_root = tmp_path / "existing-root"
    existing_root.mkdir()
    connection = V1Connection(
        name="default-artifacts",
        kind=V1ConnectionKind.VOLUME_CLAIM,
        schema_=V1ClaimConnection(volume_claim="claim", mount_path=str(existing_root)),
    )
    set_default_artifacts_store(connection)
    patch_fs(monkeypatch, fs, str(existing_root))
    monkeypatch.setattr(connection_check, "_read_mount_points", lambda: [])

    data = run_default_check()

    assert data["status"] == "failed"
    assert data["results"][0]["checks"][0]["code"] == (
        "connection_mount_path_not_mounted"
    )
    assert fs.operations == []


def test_check_mount_information_failure(tmp_path, monkeypatch):
    fs = FakeFS()
    mounted_root = tmp_path / "mounted-root"
    mounted_root.mkdir()
    connection = V1Connection(
        name="default-artifacts",
        kind=V1ConnectionKind.HOST_PATH,
        schema_=V1HostPathConnection(
            host_path=str(mounted_root), mount_path=str(mounted_root)
        ),
    )
    set_default_artifacts_store(connection)
    patch_fs(monkeypatch, fs, str(mounted_root))

    def read_mount_points():
        raise PermissionError("Mount information is unavailable")

    monkeypatch.setattr(connection_check, "_read_mount_points", read_mount_points)

    data = run_default_check()

    assert data["status"] == "failed"
    assert data["results"][0]["checks"][0]["code"] == (
        "connection_mount_path_check_failed"
    )
    assert fs.operations == []


def test_check_default_read_only_artifacts_store_requires_write(tmp_path, monkeypatch):
    fs = FakeFS()
    fs._pipe = AsyncMock(side_effect=PermissionError("Read-only filesystem"))
    mounted_root = tmp_path / "mounted-root"
    mounted_root.mkdir()
    connection = V1Connection(
        name="default-artifacts",
        kind=V1ConnectionKind.HOST_PATH,
        schema_=V1HostPathConnection(
            host_path=str(mounted_root),
            mount_path=str(mounted_root),
            read_only=True,
        ),
    )
    set_default_artifacts_store(connection)
    patch_fs(monkeypatch, fs, str(mounted_root))
    monkeypatch.setattr(
        connection_check, "_read_mount_points", lambda: [str(mounted_root)]
    )

    data = run_default_check()

    assert data["status"] == "failed"
    assert [check["name"] for check in data["results"][0]["checks"]] == ["access"]
    assert data["results"][0]["checks"][0]["code"] == "artifacts_store_access_failed"
    fs._pipe.assert_awaited_once()
    assert fs.operations == []


def test_check_storage_read_failure_cleans_up(monkeypatch, caplog):
    fs = FakeFS()
    fs.cat_error = PermissionError("token=super-secret")
    set_default_artifacts_store(make_bucket_connection(V1ConnectionKind.GCS))
    patch_fs(monkeypatch, fs, "gs://bucket")
    caplog.set_level(logging.ERROR, logger="haupt.streams.connection_check")

    data = run_default_check()

    result = data["results"][0]
    assert data["status"] == "failed"
    assert result["checks"][0]["code"] == "artifacts_store_access_failed"
    assert [operation for operation, _ in fs.operations] == ["pipe", "cat", "rm"]
    assert fs.files == {}
    assert "super-secret" not in str(data)
    assert "PermissionError: token=super-secret" in caplog.text
    assert data["results"][1]["status"] == "passed"


def test_check_storage_read_mismatch_cleans_up(monkeypatch):
    fs = FakeFS()
    fs._cat = AsyncMock(return_value=b"unexpected content")
    set_default_artifacts_store(make_bucket_connection(V1ConnectionKind.GCS))
    patch_fs(monkeypatch, fs, "gs://bucket")

    data = run_default_check()

    assert data["status"] == "failed"
    check = data["results"][0]["checks"][0]
    assert check["code"] == "artifacts_store_access_failed"
    assert check["exception"] == "ValueError"
    fs._cat.assert_awaited_once()
    assert [operation for operation, _ in fs.operations] == ["pipe", "rm"]
    assert fs.files == {}


def test_check_storage_initialization_failure_returns_sanitized_response(
    monkeypatch, caplog
):
    set_default_artifacts_store(make_bucket_connection(V1ConnectionKind.GCS))

    async def get_fs(connection=None):
        raise PermissionError("private_key=super-secret token=other-secret")

    monkeypatch.setattr(connection_check.AppFS, "get_fs", get_fs)
    caplog.set_level(logging.ERROR, logger="haupt.streams.connection_check")

    data = run_default_check()

    result = data["results"][0]
    assert data["status"] == "failed"
    assert result["checks"][0]["code"] == "artifacts_store_access_failed"
    assert result["checks"][0]["exception"] == "PermissionError"
    assert "super-secret" not in str(data)
    assert "other-secret" not in str(data)
    assert "PermissionError: private_key=super-secret token=other-secret" in caplog.text


def test_check_kubernetes_failure_returns_sanitized_response(monkeypatch, caplog):
    managers = []
    fs = FakeFS()
    set_default_artifacts_store(make_bucket_connection(V1ConnectionKind.GCS))
    patch_fs(monkeypatch, fs, "gs://bucket")

    class FailingK8sManager:
        def __init__(self, namespace, in_cluster):
            self.closed = False
            managers.append(self)

        async def setup(self):
            raise RuntimeError("token=super-secret")

        async def close(self):
            self.closed = True

    monkeypatch.setattr(connection_check, "AsyncK8sManager", FailingK8sManager)
    caplog.set_level(logging.ERROR, logger="haupt.streams.connection_check")

    data = run_default_check()

    result = data["results"][1]
    assert data["status"] == "failed"
    assert result["checks"][0]["code"] == "kubernetes_setup_failed"
    assert result["checks"][0]["exception"] == "RuntimeError"
    assert "super-secret" not in str(data)
    assert "RuntimeError: token=super-secret" in caplog.text
    assert managers[0].closed is True


def test_check_missing_default_artifacts_store(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_CONFIG", None)

    data = run_default_check()

    assert data["status"] == "failed"
    assert data["results"][0]["checks"][0]["code"] == (
        "default_artifacts_store_not_found"
    )
    assert data["results"][1]["status"] == "passed"


def test_check_named_connection_is_deferred(monkeypatch):
    storage_check = AsyncMock()
    kubernetes_check = AsyncMock()
    monkeypatch.setattr(connection_check, "_check_artifacts_store", storage_check)
    monkeypatch.setattr(
        connection_check, "_check_kubernetes_connection", kubernetes_check
    )

    data = asyncio.run(
        connection_check.check_named_agent_connection(
            connection_name="repo",
        )
    )

    assert data["status"] == "failed"
    assert data["results"][0]["connection"] == {
        "name": "repo",
        "kind": "unknown",
        "configured_sources": [],
    }
    assert data["results"][0]["checks"][0]["code"] == (
        "named_connection_check_unsupported"
    )
    storage_check.assert_not_awaited()
    kubernetes_check.assert_not_awaited()


def test_check_agent_connection_response_serializes():
    response = asyncio.run(
        agents_module.check_agent_connection(
            RequestFactory().post(
                "/streams/v1/default/foo/agents/uuid/connections_check",
                data={"connection": "repo"},
                content_type="application/json",
            ),
            namespace="default",
            owner="foo",
            agent_uuid="uuid",
            methods=["POST"],
        )
    )

    assert response.status_code == status.HTTP_200_OK
    data = orjson_loads(response.content)
    assert data["results"][0]["checks"][0]["code"] == (
        "named_connection_check_unsupported"
    )
