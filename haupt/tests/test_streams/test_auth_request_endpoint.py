import asyncio

import pytest

from django.test import RequestFactory
from rest_framework import status

from haupt.streams.endpoints import auth_request as auth_request_module
from polyaxon import settings
from polyaxon._utils.test_utils import patch_settings


pytestmark = pytest.mark.streams_mark


@pytest.fixture(autouse=True)
def patch_client_settings(tmp_path):
    patch_settings(set_auth=False, set_client=True, set_cli=False, set_agent=False)
    settings.CLIENT_CONFIG.archives_root = str(tmp_path)
    settings.CLIENT_CONFIG.timezone = "UTC"


def make_auth_request():
    return RequestFactory().get(
        "/auth-request/v1/",
        HTTP_X_ORIGIN_URI="/services/v1/ns/owner/project/runs/uuid/8000/path",
        HTTP_X_ORIGIN_METHOD="GET",
        HTTP_AUTHORIZATION="token abc",
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

    monkeypatch.setattr(auth_request_module, "_check_auth_cache", check_auth_cache)
    monkeypatch.setattr(
        auth_request_module, "_check_auth_service", fail_check_auth_service
    )

    response = asyncio.run(auth_request_module.auth_request(make_auth_request()))

    assert response.status_code == status.HTTP_200_OK
