#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from rest_framework.urlpatterns import format_suffix_patterns

from django.urls import re_path

from haupt.apis.project_resources import views
from haupt.common.apis.urls import projects

projects_urlpatterns = [
    re_path(
        projects.URLS_PROJECTS_RUNS_TAG,
        views.ProjectRunsTagView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_ARTIFACTS_LINEAGE_V0,
        views.ProjectRunsArtifactsView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_ARTIFACTS_LINEAGE,
        views.ProjectRunsArtifactsView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_STOP,
        views.ProjectRunsStopView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_APPROVE,
        views.ProjectRunsApproveView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_SYNC,
        views.ProjectRunsSyncView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_DELETE,
        views.ProjectRunsDeleteView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_LIST,
        views.ProjectRunsListView.as_view(),
    ),
]

# Order is important, because the patterns could swallow other urls
urlpatterns = format_suffix_patterns(projects_urlpatterns)
