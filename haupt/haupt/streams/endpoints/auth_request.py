import logging
import os

from typing import Dict, Optional

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
from polyaxon import settings
from polyaxon._env_vars.keys import ENV_KEYS_PROXY_LOCAL_PORT
from polyaxon.api import AUTH_V1_LOCATION

logger = logging.getLogger("haupt.streams.auth")


def _get_auth_cache_path(request_cache: str) -> str:
    auth_cache_path = os.path.join(
        settings.CLIENT_CONFIG.archives_root, ".token/{}".format(request_cache)
    )
    check_or_create_path(auth_cache_path, is_dir=False)
    return auth_cache_path


async def _check_auth_cache(request_cache: str) -> bool:
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
                interval = 60 if last_value["response"] else 30

            if (now() - last_time).seconds < interval:
                return True

            os.remove(cache_path)
        except Exception as e:
            logger.warning(
                "An error was raised while deleting some auth cache request %s" % e
            )

    return False


async def _persist_auth_cache(request_cache: str, response: bool):
    cache_path = _get_auth_cache_path(request_cache)
    data = {"time": DateTimeFormatter.format_datetime(now()), "response": response}
    async with aiofiles.open(cache_path, "w") as filepath:
        await filepath.write(orjson_dumps(data))


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
    except Exception as exc:
        return HttpResponse(
            content="Auth request failed extracting headers: %s" % exc,
            status=status.HTTP_403_FORBIDDEN,
        )

    # Check cache
    cached = await _check_auth_cache(request_cache=request_cache)
    if cached:
        return HttpResponse(status=status.HTTP_200_OK)

    if dj_settings.POLYAXON_SERVICE == "streams":
        # Contact auth service
        response = await _check_auth_service(headers=request.headers)
        if response.status != 200:
            await _persist_auth_cache(request_cache=request_cache, response=False)
            return HttpResponse(
                content="Auth request failed",
                status=status.HTTP_403_FORBIDDEN,
            )
    try:
        path, params = k8s_check(uri)
    except ValueError:
        await _persist_auth_cache(request_cache=request_cache, response=True)
        return HttpResponse(status=status.HTTP_200_OK)
    return await reverse_k8s(path="{}?{}".format(path, params))


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
