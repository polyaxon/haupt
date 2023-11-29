from clipped.utils.tz import now
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from haupt import pkg
from haupt.common import conf
from haupt.common.options.registry.installation import ORGANIZATION_ID
from haupt.db.managers.dummy_key import get_dummy_key
from polyaxon._cli.session import get_compatibility
from polyaxon._schemas.cli import CliConfig
from polyaxon._services.values import PolyaxonServices


class HealthView(APIView):
    authentication_classes = ()
    throttle_scope = "checks"
    HEALTH_FILE = "/tmp/.compatibility"

    def get_config(self):
        try:
            return CliConfig.read(self.HEALTH_FILE, config_type=".json")
        except Exception:  # noqa
            return

    def get(self, request, *args, **kwargs):
        CliConfig.init_file(self.HEALTH_FILE)
        config = self.get_config()
        if config and config.should_check():
            config.current_version = pkg.VERSION
            key = conf.get(ORGANIZATION_ID) or get_dummy_key()
            compatibility = get_compatibility(
                key=key,
                service=PolyaxonServices.PLATFORM,
                version=config.current_version,
                is_cli=False,
            )
            config.compatibility = compatibility.to_dict() if compatibility else None
            config.last_check = now()
            config.write(self.HEALTH_FILE)
        return Response(status=status.HTTP_200_OK)
