from typing import List, Optional

from django.contrib import admin
from django.urls import include, re_path
from django.views.decorators.csrf import ensure_csrf_cookie

from haupt.common import conf
from haupt.common.apis.index.errors import (
    Handler50xView,
    Handler403View,
    Handler404View,
)
from haupt.common.apis.index.views import IndexView
from haupt.common.options.registry.core import UI_ADMIN_ENABLED
from polyaxon.api import ADMIN_V1, UI_V1


def _handler500(request):
    return Handler50xView.as_view()(request)


handler404 = Handler404View.as_view()
handler403 = Handler403View.as_view()
handler500 = _handler500


def get_ui_urlpatterns(ui_urlpatterns):
    ui_patterns = [
        re_path(pattern, ensure_csrf_cookie(IndexView.as_view()), name="index")
        for pattern in ui_urlpatterns
    ]
    return [
        re_path(r"^$", ensure_csrf_cookie(IndexView.as_view()), name="index"),
        re_path(
            r"^{}$".format(UI_V1), ensure_csrf_cookie(IndexView.as_view()), name="ui"
        ),
        re_path(
            r"^{}/".format(UI_V1), include((ui_patterns, "ui_v1"), namespace="ui_v1")
        ),
    ]


def get_base_health_urlpatterns():
    from haupt.common.apis.index.health import HealthView

    return [
        re_path(r"^healthz/?$", HealthView.as_view(), name="health_check"),
    ]


def get_urlpatterns(
    app_patterns: List, no_healthz: bool = False, ui_urlpatterns: Optional[List] = None
):
    if conf.get(UI_ADMIN_ENABLED):
        admin.site.site_header = "Admin site"
        admin.site.index_title = "-"
        admin.site.site_title = "Admin site"
        app_patterns += [re_path(r"^{}/".format(ADMIN_V1), admin.site.urls)]

    urlpatterns = app_patterns
    if not no_healthz:
        urlpatterns = get_base_health_urlpatterns() + urlpatterns
    if ui_urlpatterns:
        urlpatterns += get_ui_urlpatterns(ui_urlpatterns)

    return urlpatterns
