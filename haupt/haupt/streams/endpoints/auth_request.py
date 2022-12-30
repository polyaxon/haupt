#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import logging
import os

from typing import Dict

import ujson

from rest_framework import status

from django.core.handlers.asgi import ASGIRequest
from django.db import transaction
from django.http import HttpResponse
from django.urls import path

import aiofiles
import aiohttp

from haupt.common.endpoints.validation import validate_methods
from haupt.streams.controllers.k8s_check import k8s_check, reverse_k8s
from polyaxon import settings
from polyaxon.utils.date_utils import DateTimeFormatter
from polyaxon.utils.hashing import hash_value
from polyaxon.utils.tz_utils import now

logger = logging.getLogger("haupt.streams.auth")


def _get_auth_cache_path(request_cache: str):
    return os.path.join(
        settings.CLIENT_CONFIG.archives_root, ".token/{}".format(request_cache)
    )


async def _check_auth_cache(request_cache: str) -> bool:
    cache_path = _get_auth_cache_path(request_cache)
    if os.path.isfile(cache_path):
        async with aiofiles.open(cache_path, mode="r") as f:
            last_value = ujson.loads(await f.read())
            last_time = DateTimeFormatter.extract_timestamp(
                last_value["time"],
                dt_format=DateTimeFormatter.DATETIME_FORMAT,
                timezone=settings.CLIENT_CONFIG.timezone,
                force_tz=True,
            )
            interval = 60 if last_value["response"] else 30

        if now() - last_time < interval:
            return True

        try:
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
        await filepath.write(ujson.dumps(data))


async def _check_auth_service(uri: str, headers: Dict):
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(uri, headers=headers) as resp:
            return resp


@transaction.non_atomic_requests
async def auth_request(request: ASGIRequest, methods: Dict = None) -> HttpResponse:
    validate_methods(request, methods)
    # Polyaxon checks for origin headers
    try:
        uri = request.META.get("HTTP_X_ORIGIN_URI")
        logger.info(uri)
        if not uri:
            return HttpResponse(
                content="Request must comply with an HTTP_X_ORIGIN_URI",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        method = request.META.get("HTTP_X_ORIGIN_METHOD")
        if not method:
            return HttpResponse(
                content="Request must comply with an HTTP_X_ORIGIN_METHOD",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        method = request.META.get("HTTP_X_ORIGIN_METHOD")
        if not method:
            return HttpResponse(
                content="Request must comply with an HTTP_X_ORIGIN_METHOD",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        request_cache = hash_value(value={uri, method, auth}, hash_length=64)
    except Exception as exc:
        return HttpResponse(
            content="Auth request failed extracting headers: %s" % exc,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Check cache
    cached = await _check_auth_cache(request_cache=request_cache)
    if cached:
        return HttpResponse(status_code=status.HTTP_200_OK)

    # Contact auth service
    response = await _check_auth_service(uri=uri, headers=request.headers)
    if response.status != 200:
        await _persist_auth_cache(request_cache=request_cache, response=False)
        return HttpResponse(
            content="Auth request failed",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        path, params = k8s_check(uri)
    except ValueError:
        await _persist_auth_cache(request_cache=request_cache, response=True)
        return HttpResponse(status_code=status.HTTP_200_OK)
    return await reverse_k8s(path="{}?{}".format(path, params))


URLS_RUNS_AUTH_REQUEST = "/"

# fmt: off
auth_request_routes = [
    path(
        URLS_RUNS_AUTH_REQUEST,
        auth_request,
        name="auth_request",
        kwargs=dict(methods=["GET"]),
    ),
]
