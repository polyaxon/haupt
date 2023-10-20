from rest_framework.urlpatterns import format_suffix_patterns

from django.urls import re_path

from haupt.apis.runs import views
from haupt.common.apis.urls import runs

runs_urlpatterns = [
    re_path(runs.URLS_RUNS_DETAILS, views.RunDetailView.as_view()),
    re_path(runs.URLS_RUNS_RESTART, views.RunRestartView.as_view()),
    re_path(runs.URLS_RUNS_RESUME, views.RunResumeView.as_view()),
    re_path(runs.URLS_RUNS_COPY, views.RunCopyView.as_view()),
    re_path(runs.URLS_RUNS_STOP, views.RunStopView.as_view()),
    re_path(runs.URLS_RUNS_SKIP, views.RunSkipView.as_view()),
    re_path(runs.URLS_RUNS_APPROVE, views.RunApproveView.as_view()),
    re_path(runs.URLS_RUNS_STATUSES, views.RunStatusListView.as_view()),
    re_path(runs.URLS_RUNS_NAMESPACE, views.RunNamespaceView.as_view()),
    re_path(runs.URLS_RUNS_TRANSFER, views.RunTransferView.as_view()),
    re_path(runs.URLS_RUNS_INVALIDATE, views.RunInvalidateView.as_view()),
    re_path(runs.URLS_RUNS_ARCHIVE, views.RunArchiveView.as_view()),
    re_path(runs.URLS_RUNS_RESTORE, views.RunRestoreView.as_view()),
    re_path(runs.URLS_RUNS_BOOKMARK, views.RunBookmarkCreateView.as_view()),
    re_path(runs.URLS_RUNS_UNBOOKMARK, views.RunBookmarkDeleteView.as_view()),
    re_path(runs.URLS_RUNS_STATS, views.RunStatsView.as_view()),
]

urlpatterns = format_suffix_patterns(runs_urlpatterns)
