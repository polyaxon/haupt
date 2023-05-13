from typing import Optional, Tuple

from haupt.schemas.platform_config import PlatformConfig


def set_apps(
    context,
    config: PlatformConfig,
    third_party_apps: Optional[Tuple],
    project_apps: Tuple,
    db_app: Optional[str] = None,
    use_db_apps: bool = True,
    use_admin_apps: bool = False,
    use_staticfiles_app: bool = True,
):
    extra_apps = tuple(config.extra_apps) if config.extra_apps else ()

    apps = ()
    if use_db_apps:
        apps += (
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
        )
        if use_admin_apps:
            apps += (
                "django.contrib.admin",
                "django.contrib.admindocs",
            )

    if use_staticfiles_app:
        apps += ("django.contrib.staticfiles",)

    model_apps = ()
    if use_db_apps:
        if db_app:
            model_apps = (db_app,)
        elif config.is_sqlite_db_engine:
            model_apps = ("haupt.db.sqlite.db.apps.DBConfig",)
        else:
            model_apps = ("haupt.db.pgsql.db.apps.DBConfig",)

    third_party_apps = third_party_apps or ()
    project_apps = project_apps or ()

    context["INSTALLED_APPS"] = (
        apps + third_party_apps + model_apps + extra_apps + project_apps
    )
