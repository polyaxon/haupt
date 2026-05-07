import pytest

from haupt import settings
from haupt.proxies.schemas.dns import get_dns_config, get_resolver
from haupt.proxies.schemas.services import get_sandbox_location_config
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestSandboxSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_sandbox_dns_resolver(self):
        settings.PROXIES_CONFIG.auth_enabled = False
        expected = r"""
location ~ /sandbox/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/(.+) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;
    auth_request_set $sandbox_token $upstream_http_sandbox_token;
    rewrite_log on;
    rewrite ^/sandbox/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/(.+) /$5 break;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:9090;
    proxy_http_version 1.1;
    proxy_redirect     off;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_hide_header Content-Security-Policy;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Polyaxon-Sandbox-Token $sandbox_token;
    proxy_set_header Authorization "";
    proxy_set_header Cookie "";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_use_resolver = False
        resolver = get_resolver()
        assert get_sandbox_location_config(resolver=resolver, cors="") == expected

        expected = r"""
location ~ /sandbox/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/(.+) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;
    auth_request_set $sandbox_token $upstream_http_sandbox_token;
    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/sandbox/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/(.+) /$5 break;
    proxy_pass http://plx-operation-$4.$1.svc.new-dns:9090;
    proxy_http_version 1.1;
    proxy_redirect     off;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_hide_header Content-Security-Policy;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Polyaxon-Sandbox-Token $sandbox_token;
    proxy_set_header Authorization "";
    proxy_set_header Cookie "";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.kube-system"
        settings.PROXIES_CONFIG.dns_use_resolver = True
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        resolver = get_resolver()
        assert get_sandbox_location_config(resolver=resolver, cors="") == expected

    def test_sandbox_dns_backend(self):
        settings.PROXIES_CONFIG.auth_enabled = False
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location ~ /sandbox/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/(.+) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;
    auth_request_set $sandbox_token $upstream_http_sandbox_token;
    resolver kube-dns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/sandbox/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/(.+) /$5 break;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:9090;
    proxy_http_version 1.1;
    proxy_redirect     off;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_hide_header Content-Security-Policy;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Polyaxon-Sandbox-Token $sandbox_token;
    proxy_set_header Authorization "";
    proxy_set_header Cookie "";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_dns_config() == "kube-dns.kube-system.svc.cluster.local"
        resolver = get_resolver()
        assert get_sandbox_location_config(resolver=resolver, cors="") == expected

        expected = r"""
location ~ /sandbox/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/(.+) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;
    auth_request_set $sandbox_token $upstream_http_sandbox_token;
    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/sandbox/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/(.+) /$5 break;
    proxy_pass http://plx-operation-$4.$1.svc.new-dns:9090;
    proxy_http_version 1.1;
    proxy_redirect     off;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_hide_header Content-Security-Policy;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Polyaxon-Sandbox-Token $sandbox_token;
    proxy_set_header Authorization "";
    proxy_set_header Cookie "";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.kube-system.svc.new-dns"
        resolver = get_resolver()
        assert get_sandbox_location_config(resolver=resolver, cors="") == expected

    def test_sandbox_dns_prefix(self):
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location ~ /sandbox/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/(.+) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;
    auth_request_set $sandbox_token $upstream_http_sandbox_token;
    resolver coredns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/sandbox/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/(.+) /$5 break;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:9090;
    proxy_http_version 1.1;
    proxy_redirect     off;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_hide_header Content-Security-Policy;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Polyaxon-Sandbox-Token $sandbox_token;
    proxy_set_header Authorization "";
    proxy_set_header Cookie "";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_prefix = "coredns.kube-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_dns_config() == "coredns.kube-system.svc.cluster.local"
        resolver = get_resolver()
        assert get_sandbox_location_config(resolver=resolver, cors="") == expected

        expected = r"""
location ~ /sandbox/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/(.+) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;
    auth_request_set $sandbox_token $upstream_http_sandbox_token;
    resolver kube-dns.new-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/sandbox/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/(.+) /$5 break;
    proxy_pass http://plx-operation-$4.$1.svc.new-dns:9090;
    proxy_http_version 1.1;
    proxy_redirect     off;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_hide_header Content-Security-Policy;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Polyaxon-Sandbox-Token $sandbox_token;
    proxy_set_header Authorization "";
    proxy_set_header Cookie "";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.new-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.new-system.svc.new-dns"
        resolver = get_resolver()
        assert get_sandbox_location_config(resolver=resolver, cors="") == expected
