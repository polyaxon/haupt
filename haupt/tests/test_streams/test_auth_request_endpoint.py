import asyncio

from unittest.mock import patch

import pytest

from django.http import HttpResponse
from django.test import RequestFactory
from rest_framework import status

from haupt.streams.endpoints import auth_request as auth_request_module
from polyaxon import settings
from polyaxon._env_vars.keys import ENV_KEYS_SECRET_INTERNAL_TOKEN
from polyaxon._sandbox.auth import derive_sandbox_token
from polyaxon._utils.test_utils import patch_settings


pytestmark = pytest.mark.streams_mark


@pytest.fixture(autouse=True)
def patch_client_settings(tmp_path, monkeypatch):
    patch_settings(set_auth=False, set_client=True, set_cli=False, set_agent=False)
    settings.CLIENT_CONFIG.archives_root = str(tmp_path)
    settings.CLIENT_CONFIG.timezone = "UTC"
    monkeypatch.setattr(
        auth_request_module.dj_settings,
        "POLYAXON_SERVICE",
        "streams",
        raising=False,
    )


class AuthResponse:
    status = status.HTTP_200_OK


class AuthDeniedResponse:
    status = status.HTTP_403_FORBIDDEN


def make_auth_request(
    uri="/services/v1/ns/owner/project/runs/uuid/8000/path",
    method="GET",
    auth="token abc",
):
    return RequestFactory().get(
        "/auth-request/v1/",
        HTTP_X_ORIGIN_URI=uri,
        HTTP_X_ORIGIN_METHOD=method,
        HTTP_AUTHORIZATION=auth,
    )


def test_auth_cache_distinguishes_allow_deny_and_miss():
    asyncio.run(
        auth_request_module._persist_auth_cache(
            request_cache="cached-allow", response=True
        )
    )
    asyncio.run(
        auth_request_module._persist_auth_cache(
            request_cache="cached-deny", response=False
        )
    )

    assert asyncio.run(auth_request_module._check_auth_cache("cached-allow")) is True
    assert asyncio.run(auth_request_module._check_auth_cache("cached-deny")) is False
    assert asyncio.run(auth_request_module._check_auth_cache("missing")) is None


def test_uri_family_uses_path_not_query_string():
    assert (
        auth_request_module._get_uri_family(
            "/services/v1/ns/owner/project/runs/uuid/8000/path"
            "?next=/sandbox/v1/ns/owner/project/runs/uuid/ping"
        )
        == auth_request_module.URI_FAMILY_OTHER
    )


def test_auth_request_rejects_cached_deny(monkeypatch):
    async def check_auth_cache(request_cache):
        return False

    async def fail_check_auth_service(headers):
        raise AssertionError("cached deny must not call auth service")

    async def fail_persist_auth_cache(request_cache, response):
        raise AssertionError("cached deny must not persist a new cache entry")

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", check_auth_cache)
    monkeypatch.setattr(
        auth_request_module, "_check_auth_service", fail_check_auth_service
    )
    monkeypatch.setattr(
        auth_request_module, "_persist_auth_cache", fail_persist_auth_cache
    )

    response = asyncio.run(auth_request_module.auth_request(make_auth_request()))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.content == b"Auth request failed (cached)"


def test_auth_request_allows_cached_allow(monkeypatch):
    async def check_auth_cache(request_cache):
        return True

    async def fail_check_auth_service(headers):
        raise AssertionError("cached allow must not call auth service")

    async def fail_persist_auth_cache(request_cache, response):
        raise AssertionError("cached allow must not persist a new cache entry")

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", check_auth_cache)
    monkeypatch.setattr(
        auth_request_module, "_check_auth_service", fail_check_auth_service
    )
    monkeypatch.setattr(
        auth_request_module, "_persist_auth_cache", fail_persist_auth_cache
    )

    response = asyncio.run(auth_request_module.auth_request(make_auth_request()))

    assert response.status_code == status.HTTP_200_OK


def test_auth_request_caches_regular_auth_allow(monkeypatch):
    persisted = []

    async def check_auth_cache(request_cache):
        return None

    async def check_auth_service(headers):
        return AuthResponse()

    async def persist_auth_cache(request_cache, response):
        persisted.append(response)

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", check_auth_cache)
    monkeypatch.setattr(auth_request_module, "_check_auth_service", check_auth_service)
    monkeypatch.setattr(auth_request_module, "_persist_auth_cache", persist_auth_cache)

    response = asyncio.run(auth_request_module.auth_request(make_auth_request()))

    assert response.status_code == status.HTTP_200_OK
    assert persisted == [True]


def test_auth_request_caches_regular_auth_deny(monkeypatch):
    persisted = []

    async def check_auth_cache(request_cache):
        return None

    async def check_auth_service(headers):
        return AuthDeniedResponse()

    async def persist_auth_cache(request_cache, response):
        persisted.append(response)

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", check_auth_cache)
    monkeypatch.setattr(auth_request_module, "_check_auth_service", check_auth_service)
    monkeypatch.setattr(auth_request_module, "_persist_auth_cache", persist_auth_cache)

    response = asyncio.run(auth_request_module.auth_request(make_auth_request()))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.content == b"Auth request failed"
    assert persisted == [False]


def test_auth_request_non_streams_cache_miss_does_not_persist_allow(monkeypatch):
    async def check_auth_cache(request_cache):
        return None

    async def fail_check_auth_service(headers):
        raise AssertionError("non-streams auth request must not call auth service")

    async def fail_persist_auth_cache(request_cache, response):
        raise AssertionError("non-streams cache miss must not persist auth cache")

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", check_auth_cache)
    monkeypatch.setattr(
        auth_request_module, "_check_auth_service", fail_check_auth_service
    )
    monkeypatch.setattr(
        auth_request_module, "_persist_auth_cache", fail_persist_auth_cache
    )
    monkeypatch.setattr(
        auth_request_module.dj_settings,
        "POLYAXON_SERVICE",
        "api",
        raising=False,
    )

    response = asyncio.run(auth_request_module.auth_request(make_auth_request()))

    assert response.status_code == status.HTTP_200_OK


def test_auth_request_sandbox_cached_allow_returns_token(monkeypatch):
    async def check_auth_cache(request_cache):
        return True

    async def fail_check_auth_service(headers):
        raise AssertionError("cached sandbox allow must not call auth service")

    async def fail_persist_auth_cache(request_cache, response):
        raise AssertionError("cached sandbox allow must not persist auth cache")

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", check_auth_cache)
    monkeypatch.setattr(
        auth_request_module, "_check_auth_service", fail_check_auth_service
    )
    monkeypatch.setattr(
        auth_request_module, "_persist_auth_cache", fail_persist_auth_cache
    )

    with patch.dict(
        "os.environ", {ENV_KEYS_SECRET_INTERNAL_TOKEN: "internal-token"}
    ):
        response = asyncio.run(
            auth_request_module.auth_request(
                make_auth_request(uri="/sandbox/v1/ns/owner/project/runs/uuid/ping")
            )
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["SANDBOX_TOKEN"] == derive_sandbox_token(
        "internal-token", "uuid"
    )


def test_auth_request_sandbox_cache_miss_persists_allow_and_returns_token(monkeypatch):
    persisted = []

    async def check_auth_cache(request_cache):
        return None

    async def check_auth_service(headers):
        return AuthResponse()

    async def persist_auth_cache(request_cache, response):
        persisted.append(response)

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", check_auth_cache)
    monkeypatch.setattr(auth_request_module, "_check_auth_service", check_auth_service)
    monkeypatch.setattr(auth_request_module, "_persist_auth_cache", persist_auth_cache)

    with patch.dict(
        "os.environ", {ENV_KEYS_SECRET_INTERNAL_TOKEN: "internal-token"}
    ):
        response = asyncio.run(
            auth_request_module.auth_request(
                make_auth_request(uri="/sandbox/v1/ns/owner/project/runs/uuid/ping")
            )
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["SANDBOX_TOKEN"] == derive_sandbox_token(
        "internal-token", "uuid"
    )
    assert persisted == [True]


def test_auth_request_sandbox_cached_deny_stops_before_token(monkeypatch):
    async def check_auth_cache(request_cache):
        return False

    async def fail_check_auth_service(headers):
        raise AssertionError("cached sandbox deny must not call auth service")

    async def fail_persist_auth_cache(request_cache, response):
        raise AssertionError("cached sandbox deny must not persist auth cache")

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", check_auth_cache)
    monkeypatch.setattr(
        auth_request_module, "_check_auth_service", fail_check_auth_service
    )
    monkeypatch.setattr(
        auth_request_module, "_persist_auth_cache", fail_persist_auth_cache
    )

    response = asyncio.run(
        auth_request_module.auth_request(
            make_auth_request(uri="/sandbox/v1/ns/owner/project/runs/uuid/ping")
        )
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.content == b"Auth request failed (cached)"


def test_auth_request_sandbox_deny_persists_auth_deny(monkeypatch):
    persisted = []

    async def check_auth_cache(request_cache):
        return None

    async def check_auth_service(headers):
        return AuthDeniedResponse()

    async def persist_auth_cache(request_cache, response):
        persisted.append(response)

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", check_auth_cache)
    monkeypatch.setattr(auth_request_module, "_check_auth_service", check_auth_service)
    monkeypatch.setattr(auth_request_module, "_persist_auth_cache", persist_auth_cache)

    response = asyncio.run(
        auth_request_module.auth_request(
            make_auth_request(uri="/sandbox/v1/ns/owner/project/runs/uuid/ping")
        )
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.content == b"Auth request failed"
    assert persisted == [False]


def test_auth_request_sandbox_rejects_invalid_path_before_cache(monkeypatch):
    async def fail_check_auth_cache(request_cache):
        raise AssertionError("invalid sandbox path must not read auth cache")

    async def fail_check_auth_service(headers):
        raise AssertionError("invalid sandbox path must not call auth service")

    async def fail_persist_auth_cache(request_cache, response):
        raise AssertionError("invalid sandbox path must not persist auth cache")

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", fail_check_auth_cache)
    monkeypatch.setattr(
        auth_request_module, "_check_auth_service", fail_check_auth_service
    )
    monkeypatch.setattr(
        auth_request_module, "_persist_auth_cache", fail_persist_auth_cache
    )

    response = asyncio.run(
        auth_request_module.auth_request(
            make_auth_request(uri="/sandbox/v1/ns/owner/project/runs/uuid/")
        )
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.content == b"A valid sandbox path param is required"


def test_auth_request_k8s_cached_allow_returns_dynamic_headers(monkeypatch):
    async def check_auth_cache(request_cache):
        return True

    async def fail_check_auth_service(headers):
        raise AssertionError("cached k8s allow must not call auth service")

    async def fail_persist_auth_cache(request_cache, response):
        raise AssertionError("cached k8s allow must not persist auth cache")

    async def reverse_k8s(path):
        assert (
            path
            == "api/v1/namespaces/ns/pods/pod/exec?command=/bin/bash&container=main"
        )
        return HttpResponse(
            status=status.HTTP_200_OK,
            headers={
                "K8S_URI": "https://k8s.local/exec",
                "K8S_TOKEN": "k8s-token",
            },
        )

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", check_auth_cache)
    monkeypatch.setattr(
        auth_request_module, "_check_auth_service", fail_check_auth_service
    )
    monkeypatch.setattr(
        auth_request_module, "_persist_auth_cache", fail_persist_auth_cache
    )
    monkeypatch.setattr(auth_request_module, "reverse_k8s", reverse_k8s)

    response = asyncio.run(
        auth_request_module.auth_request(
            make_auth_request(
                uri=(
                    "/k8s/v1/ns/owner/project/runs/uuid/k8s_exec/pod/main"
                    "?command=/bin/bash"
                )
            )
        )
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["K8S_URI"] == "https://k8s.local/exec"
    assert response.headers["K8S_TOKEN"] == "k8s-token"


def test_auth_request_k8s_cache_miss_persists_allow_and_returns_dynamic_headers(
    monkeypatch,
):
    persisted = []

    async def check_auth_cache(request_cache):
        return None

    async def check_auth_service(headers):
        return AuthResponse()

    async def persist_auth_cache(request_cache, response):
        persisted.append(response)

    async def reverse_k8s(path):
        assert (
            path
            == "api/v1/namespaces/ns/pods/pod/exec?command=/bin/bash&container=main"
        )
        return HttpResponse(
            status=status.HTTP_200_OK,
            headers={
                "K8S_URI": "https://k8s.local/exec",
                "K8S_TOKEN": "k8s-token",
            },
        )

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", check_auth_cache)
    monkeypatch.setattr(auth_request_module, "_check_auth_service", check_auth_service)
    monkeypatch.setattr(auth_request_module, "_persist_auth_cache", persist_auth_cache)
    monkeypatch.setattr(auth_request_module, "reverse_k8s", reverse_k8s)

    response = asyncio.run(
        auth_request_module.auth_request(
            make_auth_request(
                uri=(
                    "/k8s/v1/ns/owner/project/runs/uuid/k8s_exec/pod/main"
                    "?command=/bin/bash"
                )
            )
        )
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["K8S_URI"] == "https://k8s.local/exec"
    assert response.headers["K8S_TOKEN"] == "k8s-token"
    assert persisted == [True]
