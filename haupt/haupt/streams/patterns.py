#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.urls import include, re_path

from haupt.common.apis.index import get_urlpatterns, handler403, handler404, handler500
from haupt.streams.endpoints.artifacts import artifacts_routes
from haupt.streams.endpoints.auth_request import auth_request_routes
from haupt.streams.endpoints.base import base_health_route
from haupt.streams.endpoints.events import events_routes
from haupt.streams.endpoints.k8s import k8s_routes
from haupt.streams.endpoints.logs import internal_logs_routes, logs_routes
from haupt.streams.endpoints.notifications import notifications_routes
from haupt.streams.endpoints.sandbox import sandbox_routes
from polyaxon.api import AUTH_REQUEST_V1, INTERNAL_V1, STREAMS_V1

streams_routes = (
    logs_routes
    + k8s_routes
    + notifications_routes
    + artifacts_routes
    + events_routes
    + sandbox_routes
)

app_urlpatterns = [
    re_path(
        r"^{}/".format(INTERNAL_V1),
        include((internal_logs_routes, "internal-v1"), namespace="internal-v1"),
    ),
    re_path(
        r"^{}/".format(AUTH_REQUEST_V1),
        include((auth_request_routes, "auth-request-v1"), namespace="auth-request-v1"),
    ),
    re_path(
        r"^{}/".format(STREAMS_V1),
        include((streams_routes, "streams-v1"), namespace="streams-v1"),
    ),
    base_health_route,
]

handler404 = handler404
handler403 = handler403
handler500 = handler500
urlpatterns = get_urlpatterns(app_patterns=app_urlpatterns, no_healthz=True)
