import os

from haupt.schemas.platform_config import PlatformConfig
from polyaxon.api import STATIC_V1


def set_assets(context, config: PlatformConfig):
    context["MEDIA_ROOT"] = config.media_root
    context["MEDIA_URL"] = config.media_url

    context["STATIC_ROOT"] = config.static_root or str(config.root_dir / "static")
    context["STATIC_URL"] = config.static_url or "/static/"

    # Additional locations of static files
    public_dir = str(config.root_dir / "public")
    if os.path.exists(public_dir):
        context["STATICFILES_DIRS"] = (public_dir,)

    context["STATICFILES_FINDERS"] = (
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    )

    context["LOCALE_PATHS"] = (
        str(config.root_dir / "locale"),
        str(config.root_dir / "client" / "js" / "libs" / "locale"),
    )

    context["STATICI18N_ROOT"] = STATIC_V1
    context["STATICI18N_OUTPUT_DIR"] = "jsi18n"

    context["ARTIFACTS_ROOT"] = config.artifacts_root or "/tmp/plx/artifacts_uploads"
    context["ARCHIVES_ROOT"] = config.archives_root or "/tmp/plx/archives"
