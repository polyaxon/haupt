#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import os

from django.core.handlers.asgi import ASGIRequest
from django.urls import path

# from starlette.staticfiles import StaticFiles
# from starlette.templating import Jinja2Templates
from django.views.generic import TemplateView

from haupt import pkg
from haupt.streams.endpoints.base import UJSONResponse
from polyaxon import dist
from polyaxon.api import API_V1_LOCATION
from polyaxon.env_vars.keys import EV_KEYS_STATIC_ROOT

static_root = os.environ.get(EV_KEYS_STATIC_ROOT, os.path.dirname(__file__))
templates_path = os.path.join(static_root, "templates")

# templates = Jinja2Templates(directory=templates_path)


class IndexView(TemplateView):
    template_name = "base/index.html"


async def installation(request: ASGIRequest):
    from polyaxon.cli.session import get_installation_key

    key = get_installation_key(None)
    data = {
        "key": key,
        "version": pkg.VERSION,
        "dist": dist.SANDBOX,
    }
    return UJSONResponse(data)


# class GzipStaticFiles(StaticFiles):
#     async def get_response(self, path: str, scope):
#         response = await super().get_response(path, scope)
#         if "gz" in path:
#             response._headers["content-encoding"] = "gzip"
#         return response


home_routes = [
    path(API_V1_LOCATION + "installation", installation),
    # Mount("/static", GzipStaticFiles(directory=static_root), name="static"),
    path("/", IndexView.as_view()),
    path("/ui/{any:path}", IndexView.as_view()),
]
