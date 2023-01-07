#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from rest_framework.urlpatterns import format_suffix_patterns

from django.urls import re_path

from haupt.apis.run_lineage import views
from haupt.common.apis.urls import runs

run_lineages_urlpatterns = [
    re_path(
        runs.URLS_RUNS_ARTIFACTS_LINEAGE_LIST_V0, views.RunArtifactListView.as_view()
    ),
    re_path(
        runs.URLS_RUNS_ARTIFACTS_LINEAGE_NAMES_V0,
        views.RunArtifactNameListView.as_view(),
    ),
    re_path(
        runs.URLS_RUNS_ARTIFACTS_LINEAGE_DETAILS_V0,
        views.RunArtifactDetailView.as_view(),
    ),
    re_path(runs.URLS_RUNS_ARTIFACTS_LINEAGE_LIST, views.RunArtifactListView.as_view()),
    re_path(
        runs.URLS_RUNS_ARTIFACTS_LINEAGE_NAMES, views.RunArtifactNameListView.as_view()
    ),
    re_path(
        runs.URLS_RUNS_ARTIFACTS_LINEAGE_DETAILS, views.RunArtifactDetailView.as_view()
    ),
]

# Order is important, because the patterns could swallow other urls
urlpatterns = format_suffix_patterns(run_lineages_urlpatterns)
