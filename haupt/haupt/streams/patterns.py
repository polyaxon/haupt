from django.urls import include, re_path

from haupt import settings
from haupt.common.apis.index import get_urlpatterns, handler403, handler404, handler500
from haupt.common.apis.regex import OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN
from haupt.streams.endpoints.agents import agent_routes, internal_agent_routes
from haupt.streams.endpoints.artifacts import artifacts_routes
from haupt.streams.endpoints.auth_request import auth_request_routes
from haupt.streams.endpoints.base import base_health_route
from haupt.streams.endpoints.events import events_routes
from haupt.streams.endpoints.k8s import k8s_routes
from haupt.streams.endpoints.logs import internal_logs_routes, logs_routes
from haupt.streams.endpoints.notifications import notifications_routes
from haupt.streams.endpoints.viewer import viewer_routes
from polyaxon.api import API_V1, AUTH_REQUEST_V1, INTERNAL_V1, STREAMS_V1

is_viewer = settings.SANDBOX_CONFIG and settings.SANDBOX_CONFIG.is_viewer

streams_routes = (
    agent_routes
    + logs_routes
    + k8s_routes
    + notifications_routes
    + artifacts_routes
    + events_routes
)

app_urlpatterns = []

if is_viewer:
    app_urlpatterns += [
        re_path(
            r"^{}/".format(API_V1),
            include((viewer_routes, "local-v1"), namespace="local-v1"),
        ),
    ]

app_urlpatterns += [
    re_path(
        r"^{}/".format(INTERNAL_V1),
        include(
            (internal_agent_routes + internal_logs_routes, "internal-v1"),
            namespace="internal-v1",
        ),
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

# UI
if is_viewer:
    projects_urls = "{}/{}".format(OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN)
    orgs_urls = "orgs/{}".format(OWNER_NAME_PATTERN)
    ui_urlpatterns = [
        r"^$",
        r"^{}/?".format(orgs_urls),
        r"^{}/projects/?".format(orgs_urls),
        r"^{}/?$".format(projects_urls),
        r"^{}/runs.*/?".format(projects_urls),
        r"^{}/jobs.*/?".format(projects_urls),
        r"^{}/cli.*/?".format(projects_urls),
    ]
else:
    ui_urlpatterns = None

handler404 = handler404
handler403 = handler403
handler500 = handler500
urlpatterns = get_urlpatterns(
    app_patterns=app_urlpatterns, no_healthz=True, ui_urlpatterns=ui_urlpatterns
)
