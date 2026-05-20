from django.urls import re_path
from rest_framework.urlpatterns import format_suffix_patterns

from haupt.apis.users import views
from haupt.common.apis.regex import UUID_PATTERN


urlpatterns = [
    re_path(r"^users/ssh-keys/?$", views.UserSshKeyListCreateView.as_view()),
    re_path(
        r"^users/ssh-keys/{}/?$".format(UUID_PATTERN),
        views.UserSshKeyDetailView.as_view(),
    ),
]

urlpatterns = format_suffix_patterns(urlpatterns)
