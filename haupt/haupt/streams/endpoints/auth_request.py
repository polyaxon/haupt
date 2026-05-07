import logging
import os

from typing import Dict, Optional
from urllib.parse import urlparse

from clipped.utils.dates import DateTimeFormatter
from clipped.utils.hashing import hash_value
from clipped.utils.json import orjson_dumps, orjson_loads
from clipped.utils.paths import check_or_create_path
from clipped.utils.tz import now
from rest_framework import status

from django.conf import settings as dj_settings
from django.core.handlers.asgi import ASGIRequest
from django.db import transaction
from django.http import HttpResponse
from django.urls import path

import aiofiles
import aiohttp

from haupt.common.endpoints.validation import validate_methods
from haupt.common.headers import (
    get_authorization_header,
    get_original_method_header,
    get_original_uri_header,
)
from haupt.streams.controllers.k8s_check import k8s_check, reverse_k8s
from haupt.streams.controllers.sandbox_check import sandbox_check, reverse_sandbox
from polyaxon import settings
from polyaxon._env_vars.keys import ENV_KEYS_PROXY_LOCAL_PORT
from polyaxon.api import AUTH_V1_LOCATION, K8S_V1_LOCATION, SANDBOX_V1_LOCATION

logger = logging.getLogger("haupt.streams.auth")

URI_FAMILY_K8S = "k8s"
URI_FAMILY_SANDBOX = "sandbox"
URI_FAMILY_OTHER = "other"


def _get_uri_family(uri: str) -> str:
    path = urlparse(uri).path
    if path.startswith(SANDBOX_V1_LOCATION):
        return URI_FAMILY_SANDBOX
    if path.startswith(K8S_V1_LOCATION):
        return URI_FAMILY_K8S
    return URI_FAMILY_OTHER


def _get_auth_cache_path(request_cache: str) -> str:
    auth_cache_path = os.path.join(
        settings.CLIENT_CONFIG.archives_root, ".token/{}".format(request_cache)
    )
    check_or_create_path(auth_cache_path, is_dir=False)
    return auth_cache_path


async def _check_auth_cache(request_cache: str) -> Optional[bool]:
    cache_path = _get_auth_cache_path(request_cache)
    if os.path.isfile(cache_path):
        try:
            async with aiofiles.open(cache_path, mode="r") as f:
                last_value = orjson_loads(await f.read())
                last_time = DateTimeFormatter.extract_timestamp(
                    last_value["time"],
                    dt_format=DateTimeFormatter.DATETIME_FORMAT,
                    timezone=settings.CLIENT_CONFIG.timezone,
                    force_tz=True,
                )
                interval = 60 if last_value["response"] else 5

            if (now() - last_time).seconds < interval:
                return last_value["response"]

            os.remove(cache_path)
        except Exception as e:
            logger.warning(
                "An error was raised while deleting some auth cache request %s" % e
            )

    return None


async def _persist_auth_cache(request_cache: str, response: bool):
    cache_path = _get_auth_cache_path(request_cache)
    data = {"time": DateTimeFormatter.format_datetime(now()), "response": response}
    async with aiofiles.open(cache_path, "w") as outfile:
        await outfile.write(orjson_dumps(data))


async def _check_auth_service(headers: Dict):
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(
            "http://localhost:{}{}".format(
                os.environ[ENV_KEYS_PROXY_LOCAL_PORT], AUTH_V1_LOCATION
            ),
            headers=headers,
        ) as resp:
            return resp


@transaction.non_atomic_requests
async def auth_request(
    request: ASGIRequest, methods: Optional[Dict] = None
) -> HttpResponse:
    validate_methods(request, methods)
    # Polyaxon checks for origin headers
    try:
        uri = get_original_uri_header(request)
        logger.debug("Authenticating %s" % uri)
        if not uri:
            return HttpResponse(
                content="Request must comply with an HTTP_X_ORIGIN_URI",
                status=status.HTTP_403_FORBIDDEN,
            )
        method = get_original_method_header(request)
        if not method:
            return HttpResponse(
                content="Request must comply with an HTTP_X_ORIGIN_METHOD",
                status=status.HTTP_403_FORBIDDEN,
            )
        auth = get_authorization_header(request)
        request_cache = hash_value(
            value={uri.split("?")[0], method, auth}, hash_length=64
        )
        uri_family = _get_uri_family(uri)
    except Exception as exc:
        return HttpResponse(
            content="Auth request failed extracting headers: %s" % exc,
            status=status.HTTP_403_FORBIDDEN,
        )

    sandbox_run_uuid = None
    if uri_family == URI_FAMILY_SANDBOX:
        try:
            sandbox_run_uuid = sandbox_check(uri)
        except ValueError:
            return HttpResponse(
                content="A valid sandbox path param is required",
                status=status.HTTP_400_BAD_REQUEST,
            )

    cached = await _check_auth_cache(request_cache=request_cache)
    if cached is False:
        return HttpResponse(content="Auth request failed (cached)", status=403)

    if cached is None and dj_settings.POLYAXON_SERVICE == "streams":
        # Contact auth service
        response = await _check_auth_service(headers=request.headers)
        if response.status != 200:
            await _persist_auth_cache(request_cache=request_cache, response=False)
            return HttpResponse(
                content="Auth request failed",
                status=status.HTTP_403_FORBIDDEN,
            )
        await _persist_auth_cache(request_cache=request_cache, response=True)

    if uri_family == URI_FAMILY_SANDBOX:
        return reverse_sandbox(run_uuid=sandbox_run_uuid)

    if uri_family == URI_FAMILY_K8S:
        try:
            _path, params = k8s_check(uri)
            return await reverse_k8s(path="{}?{}".format(_path, params))
        except ValueError:
            pass

    return HttpResponse(status=status.HTTP_200_OK)


URLS_RUNS_AUTH_REQUEST = ""

# fmt: off
auth_request_routes = [
    path(
        URLS_RUNS_AUTH_REQUEST,
        auth_request,
        name="auth_request",
        kwargs=dict(methods=["GET"]),
    ),
]
