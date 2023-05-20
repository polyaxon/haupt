from rest_framework import status
from rest_framework.response import Response

from haupt.common import conf
from haupt.common.apis.regex import INSTALLATION_KEY, NAME_KEY, VERSION_KEY
from haupt.common.endpoints.base import BaseEndpoint, RetrieveEndpoint
from haupt.common.options.registry.installation import (
    ORGANIZATION_KEY,
    PLATFORM_DIST,
    PLATFORM_VERSION,
)
from haupt.db.managers.dummy_key import get_dummy_key
from polyaxon.cli.session import get_compatibility


class VersionsInstalledView(BaseEndpoint, RetrieveEndpoint):
    ALLOWED_METHODS = ["GET"]

    def retrieve(self, request, *args, **kwargs):
        data = {
            "key": conf.get(ORGANIZATION_KEY) or get_dummy_key(),
            "version": conf.get(PLATFORM_VERSION),
            "dist": conf.get(PLATFORM_DIST),
        }
        return Response(data)


class VersionsCompatibilityView(BaseEndpoint, RetrieveEndpoint):
    ALLOWED_METHODS = ["GET"]
    CONTEXT_KEYS = (INSTALLATION_KEY, VERSION_KEY, NAME_KEY)

    def get(self, request, *args, **kwargs):
        compatibility = get_compatibility(
            key=self.installation,
            service=self.name,
            version=self.version,
            is_cli=False,
            set_config=False,
        )
        return Response(
            data=compatibility.to_dict() if compatibility else {},
            status=status.HTTP_200_OK,
        )
