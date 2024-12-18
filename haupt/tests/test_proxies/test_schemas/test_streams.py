import pytest

from haupt import settings
from haupt.proxies.schemas.auth import get_auth_config
from haupt.proxies.schemas.dns import get_dns_config, get_resolver
from haupt.proxies.schemas.services import get_streams_location_config
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestStreamsSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_streams_location_with_auth_config(self):
        expected = r"""
location /streams/ {
    proxy_pass http://polyaxon-polyaxon-streams;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa

        assert get_streams_location_config(resolver="", cors="", auth="") == expected

        settings.PROXIES_CONFIG.streams_port = 8888
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.streams_host = "foo"
        expected = r"""
location /streams/ {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    proxy_pass http://foo:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        assert (
            get_streams_location_config(resolver="", cors="", auth=get_auth_config())
            == expected
        )

    def test_streams_location_with_dns_prefix(self):
        settings.PROXIES_CONFIG.auth_enabled = False
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location /streams/ {
    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://polyaxon-polyaxon-streams;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_prefix = "coredns.kube-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_dns_config() == "coredns.kube-system.svc.cluster.local"
        resolver = get_resolver()
        assert (
            get_streams_location_config(resolver=resolver, cors="", auth="") == expected
        )

        expected = r"""
location /streams/ {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.new-system.svc.new-dns valid=5s;
    proxy_pass http://polyaxon-polyaxon-streams;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.new-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.new-system.svc.new-dns"
        resolver = get_resolver()
        assert (
            get_streams_location_config(
                resolver=resolver, cors="", auth=get_auth_config()
            )
            == expected
        )
