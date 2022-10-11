#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.urls import include, re_path

from haupt.common.apis.index import get_urlpatterns, handler403, handler404, handler500
from haupt.streams.endpoints.artifacts import artifacts_routes
from haupt.streams.endpoints.base import base_routes
from haupt.streams.endpoints.events import events_routes
from haupt.streams.endpoints.index import home_routes
from haupt.streams.endpoints.k8s import k8s_routes
from haupt.streams.endpoints.logs import logs_routes
from haupt.streams.endpoints.notifications import notifications_routes
from haupt.streams.endpoints.sandbox import sandbox_routes
from polyaxon.api import STREAMS_V1

api_patterns = [
    re_path(
        r"", include(("haupt.apis.versions.urls", "versions"), namespace="versions")
    ),
]

streams_routes = (
    logs_routes
    + k8s_routes
    + notifications_routes
    + artifacts_routes
    + events_routes
    + sandbox_routes
    + base_routes
    + home_routes
)

app_urlpatterns = [
    re_path(
        r"^{}/".format(STREAMS_V1),
        include((streams_routes, "streams-v1"), namespace="streams-v1"),
    ),
    re_path(
        r"^{}/".format(STREAMS_V1),
        include((api_patterns, "api-v1"), namespace="api-v1"),
    ),
]

handler404 = handler404
handler403 = handler403
handler500 = handler500
urlpatterns = get_urlpatterns(app_urlpatterns)
