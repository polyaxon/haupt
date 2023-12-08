import pytest

from rest_framework import status

from haupt.common import conf
from haupt.common.options.registry.installation import PLATFORM_DIST, PLATFORM_VERSION
from polyaxon.api import API_V1
from tests.base.case import BaseTest


@pytest.mark.versions_mark
class TestInstallationVersionViewsV1(BaseTest):
    def setUp(self):
        super().setUp()
        self.installation_version = "/{}/installation/".format(API_V1)

    def test_version(self):
        resp = self.client.get(self.installation_version)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["version"] == conf.get(PLATFORM_VERSION)
        assert resp.data["dist"] == conf.get(PLATFORM_DIST)
        assert resp.data["mode"] is None
        assert set(resp.data.keys()) == {"dist", "key", "version", "mode"}
