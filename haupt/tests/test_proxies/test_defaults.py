import pytest

from haupt import settings
from polyaxon._contexts import paths as ctx_paths
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestSettings(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_default_values(self):
        assert settings.PROXIES_CONFIG.gateway_target_port == 8000
        assert settings.PROXIES_CONFIG.streams_target_port == 8000
        assert settings.PROXIES_CONFIG.api_target_port == 8000
        assert settings.PROXIES_CONFIG.gateway_port == 80
        assert settings.PROXIES_CONFIG.streams_port == 80
        assert settings.PROXIES_CONFIG.api_port == 80
        assert settings.PROXIES_CONFIG.streams_host == "polyaxon-polyaxon-streams"
        assert settings.PROXIES_CONFIG.api_host == "polyaxon-polyaxon-api"
        assert settings.PROXIES_CONFIG.dns_use_resolver is False
        assert settings.PROXIES_CONFIG.dns_custom_cluster == "cluster.local"
        assert settings.PROXIES_CONFIG.dns_backend == "kube-dns"
        assert settings.PROXIES_CONFIG.dns_prefix is None
        assert settings.PROXIES_CONFIG.namespace is None
        assert settings.PROXIES_CONFIG.namespaces is None
        assert settings.PROXIES_CONFIG.log_level is None
        assert settings.PROXIES_CONFIG.get_log_level() == "warn"
        assert settings.PROXIES_CONFIG.nginx_timeout == 650
        assert settings.PROXIES_CONFIG.nginx_indent_char == " "
        assert settings.PROXIES_CONFIG.nginx_indent_width == 4
        assert settings.PROXIES_CONFIG.ssl_path == "/etc/ssl/polyaxon"
        assert settings.PROXIES_CONFIG.ssl_enabled is False
        assert settings.PROXIES_CONFIG.archives_root == ctx_paths.CONTEXT_ARCHIVES_ROOT
        assert settings.PROXIES_CONFIG.ssl_path == "/etc/ssl/polyaxon"
        assert settings.PROXIES_CONFIG.ssl_enabled is False
        assert settings.PROXIES_CONFIG.auth_enabled is False
        assert settings.PROXIES_CONFIG.auth_external is None
        assert settings.PROXIES_CONFIG.auth_use_resolver is False
