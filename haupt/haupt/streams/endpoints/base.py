#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from clipped.utils.json import orjson_dumps
from rest_framework import status

from django.core.handlers.asgi import ASGIRequest
from django.http import HttpResponse
from django.urls import re_path


async def health(request: ASGIRequest) -> HttpResponse:
    return HttpResponse(status=status.HTTP_200_OK)


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
        data = orjson_dumps(data, **json_dumps_params)
        super().__init__(content=data, **kwargs)


class ConfigResponse(HttpResponse):
    def __init__(
        self,
        data,
        **kwargs,
    ):
        kwargs.setdefault("content_type", "application/json")
        super().__init__(content=data, **kwargs)


base_health_route = re_path(r"^healthz/?$", health, name="health_check")
