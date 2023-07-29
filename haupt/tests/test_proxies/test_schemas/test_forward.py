import pytest

from clipped.compact.pydantic import ValidationError

from haupt import settings
from haupt.proxies.schemas.forward import get_forward_cmd
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestGatewayForward(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_forward_config_empty(self):
        assert get_forward_cmd() is None

    def test_forward_config_wrong(self):
        assert get_forward_cmd() is None
        with self.assertRaises(ValidationError):
            settings.PROXIES_CONFIG.forward_proxy_kind = "foo"

        assert get_forward_cmd() is None
        settings.PROXIES_CONFIG.has_forward_proxy = True
        settings.PROXIES_CONFIG.forward_proxy_port = 8080
        settings.PROXIES_CONFIG.forward_proxy_host = "123.123.123.123"
        settings.PROXIES_CONFIG.api_port = 443
        settings.PROXIES_CONFIG.api_host = "cloud.polyaxon.com"
        assert get_forward_cmd() is not None

    def test_forward_config_transparent(self):
        settings.PROXIES_CONFIG.forward_proxy_kind = "transparent"
        settings.PROXIES_CONFIG.has_forward_proxy = True
        settings.PROXIES_CONFIG.forward_proxy_port = 8080
        settings.PROXIES_CONFIG.forward_proxy_host = "123.123.123.123"
        expected = """
#!/bin/bash
set -e
set -o pipefail

socat TCP4-LISTEN:8443,reuseaddr,fork TCP:123.123.123.123:8080
"""  # noqa
        assert get_forward_cmd() == expected

    def test_forward_config_connect(self):
        settings.PROXIES_CONFIG.forward_proxy_kind = "connect"
        settings.PROXIES_CONFIG.has_forward_proxy = True
        settings.PROXIES_CONFIG.forward_proxy_port = 8080
        settings.PROXIES_CONFIG.forward_proxy_host = "123.123.123.123"
        settings.PROXIES_CONFIG.api_port = 443
        settings.PROXIES_CONFIG.api_host = "cloud.polyaxon.com"
        expected = """
#!/bin/bash
set -e
set -o pipefail

socat TCP4-LISTEN:8443,reuseaddr,fork,bind=127.0.0.1 PROXY:123.123.123.123:cloud.polyaxon.com:443,proxyport=8080
"""  # noqa
        assert get_forward_cmd() == expected

    def test_forward_config_default(self):
        settings.PROXIES_CONFIG.has_forward_proxy = True
        settings.PROXIES_CONFIG.forward_proxy_port = 8080
        settings.PROXIES_CONFIG.forward_proxy_host = "123.123.123.123"
        settings.PROXIES_CONFIG.api_port = 443
        settings.PROXIES_CONFIG.api_host = "cloud.polyaxon.com"
        expected = """
#!/bin/bash
set -e
set -o pipefail

socat TCP4-LISTEN:8443,reuseaddr,fork,bind=127.0.0.1 PROXY:123.123.123.123:cloud.polyaxon.com:443,proxyport=8080
"""  # noqa
        assert get_forward_cmd() == expected
