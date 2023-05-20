from rest_framework.urlpatterns import format_suffix_patterns

from django.urls import re_path

from haupt.apis.projects import views
from haupt.common.apis.urls import projects

projects_urlpatterns = [
    re_path(projects.URLS_PROJECTS_CREATE, views.ProjectCreateView.as_view()),
    re_path(projects.URLS_PROJECTS_LIST, views.ProjectListView.as_view()),
    re_path(projects.URLS_PROJECTS_NAMES, views.ProjectNameListView.as_view()),
    re_path(projects.URLS_PROJECTS_DETAILS, views.ProjectDetailView.as_view()),
    re_path(projects.URLS_PROJECTS_ARCHIVE, views.ProjectArchiveView.as_view()),
    re_path(projects.URLS_PROJECTS_RESTORE, views.ProjectRestoreView.as_view()),
    re_path(projects.URLS_PROJECTS_BOOKMARK, views.ProjectBookmarkCreateView.as_view()),
    re_path(
        projects.URLS_PROJECTS_UNBOOKMARK, views.ProjectBookmarkDeleteView.as_view()
    ),
    re_path(projects.URLS_PROJECTS_STATS, views.ProjectStatsView.as_view()),
]

# Order is important, because the patterns could swallow other urls
urlpatterns = format_suffix_patterns(projects_urlpatterns)
