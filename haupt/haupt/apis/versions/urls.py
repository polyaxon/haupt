from rest_framework.urlpatterns import format_suffix_patterns

from django.urls import re_path

from haupt.apis.versions import views
from haupt.common.apis.urls import versions

urlpatterns = [
    re_path(versions.URLS_VERSIONS_INSTALLED, views.VersionsInstalledView.as_view()),
    re_path(
        versions.URLS_VERSIONS_COMPATIBILITY,
        views.VersionsCompatibilityView.as_view(),
    ),
]

urlpatterns = format_suffix_patterns(urlpatterns)
