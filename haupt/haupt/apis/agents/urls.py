from rest_framework.urlpatterns import format_suffix_patterns

from django.urls import re_path

from haupt.apis.agents import views
from haupt.common.apis.urls import agents

options_urlpatterns = [
    re_path(agents.URLS_CATALOGS_AGENTS_STATE, views.AgentStateViewV1.as_view()),
    re_path(agents.URLS_CATALOGS_AGENTS_CRON, views.AgentCronViewV1.as_view()),
    re_path(agents.URLS_ORGANIZATIONS_RUNS_DETAILS, views.AgentRunDetailView.as_view()),
]

urlpatterns = format_suffix_patterns(options_urlpatterns)
