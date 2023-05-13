from haupt.common.settings.apps import set_apps
from haupt.common.settings.assets import set_assets
from haupt.common.settings.core import set_core
from haupt.common.settings.cors import set_cors
from haupt.common.settings.middlewares import set_base_middlewares
from haupt.common.settings.ui import set_ui
from haupt.schemas.platform_config import PlatformConfig


def set_streams_apps(context, config: PlatformConfig):
    set_apps(
        context=context,
        config=config,
        third_party_apps=("rest_framework", "corsheaders"),
        project_apps=(
            "haupt.common.apis.apps.CommonApisConfig",
            "haupt.streams.apps.StreamsConfig",
        ),
        use_db_apps=False,
        use_staticfiles_app=context["UI_IN_SANDBOX"],
    )


def set_service(context, config: PlatformConfig):
    # This is repeated because it's required for using the staticfiles app
    context["UI_IN_SANDBOX"] = config.ui_in_sandbox
    set_streams_apps(context, config)
    set_core(context=context, config=config, use_db=False)
    set_cors(context=context, config=config)
    set_ui(context=context, config=config)
    set_base_middlewares(context=context, config=config)
    set_assets(context=context, config=config)
