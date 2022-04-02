#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import ujson

from rest_framework import status

from django.core.handlers.asgi import ASGIRequest
from django.http import HttpResponse
from django.urls import path


async def health(request: ASGIRequest) -> HttpResponse:
    return HttpResponse(status=status.HTTP_200_OK)


async def error(request: ASGIRequest):
    """
    An example error. Switch the `debug` setting to see either tracebacks or 500 pages.
    """
    raise RuntimeError("Oh no")


async def not_found(request: ASGIRequest, exc) -> HttpResponse:
    """
    Return an HTTP 404 page.
    """
    return HttpResponse(status=status.HTTP_404_NOT_FOUND)


async def server_error(request: ASGIRequest, exc):
    """
    Return an HTTP 500 page.
    """
    raise HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UJSONResponse(HttpResponse):
    def __init__(
        self,
        data,
        safe=True,
        json_dumps_params=None,
        **kwargs,
    ):
        if safe and not isinstance(data, dict):
            raise TypeError(
                "In order to allow non-dict objects to be serialized set the "
                "safe parameter to False."
            )
        if json_dumps_params is None:
            json_dumps_params = {}
        kwargs.setdefault("content_type", "application/json")
        data = ujson.dumps(data, ensure_ascii=False, **json_dumps_params)
        super().__init__(content=data, **kwargs)


class ConfigResponse(UJSONResponse):
    def __init__(
        self,
        data,
        **kwargs,
    ):
        kwargs.setdefault("content_type", "application/json")
        super().__init__(content=data, **kwargs)


base_routes = [
    path("/500", error),
    path("/healthz", health),
]

exception_handlers = {
    404: not_found,
    500: server_error,
}
