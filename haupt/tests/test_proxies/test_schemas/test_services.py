import pytest

from haupt import settings
from haupt.proxies.schemas.auth import get_auth_config
from haupt.proxies.schemas.dns import get_dns_config, get_resolver
from haupt.proxies.schemas.services import (
    get_plugins_location_config,
    get_services_location_config,
)
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestRewriteServicesSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_service_dns_resolver(self):
        settings.PROXIES_CONFIG.auth_enabled = False
        expected = r"""
location ~ /rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    rewrite_log on;
    rewrite ^/rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_use_resolver = False
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth="", rewrite=True
            )
            == expected
        )

        expected = r"""
location ~ /rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4.$1.svc.new-dns:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.kube-system"
        settings.PROXIES_CONFIG.dns_use_resolver = True
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth=get_auth_config(), rewrite=True
            )
            == expected
        )

    def test_services_dns_backend(self):
        settings.PROXIES_CONFIG.auth_enabled = False
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location ~ /rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver kube-dns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_dns_config() == "kube-dns.kube-system.svc.cluster.local"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth="", rewrite=True
            )
            == expected
        )

        expected = r"""
location ~ /rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4.$1.svc.new-dns:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.kube-system.svc.new-dns"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth=get_auth_config(), rewrite=True
            )
            == expected
        )

    def test_services_dns_prefix(self):
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location ~ /rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
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
            get_services_location_config(
                resolver=resolver, cors="", auth=get_auth_config(), rewrite=True
            )
            == expected
        )

        expected = r"""
location ~ /rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.new-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4.$1.svc.new-dns:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.new-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.new-system.svc.new-dns"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth=get_auth_config(), rewrite=True
            )
            == expected
        )


@pytest.mark.proxies_mark
class TestServicesSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_service_dns_resolver(self):
        settings.PROXIES_CONFIG.auth_enabled = False
        expected = r"""
location ~ /services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_use_resolver = False
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth="", rewrite=False
            )
            == expected
        )

        expected = r"""
location ~ /services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    proxy_pass http://plx-operation-$4.$1.svc.new-dns:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.kube-system"
        settings.PROXIES_CONFIG.dns_use_resolver = True
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth=get_auth_config(), rewrite=False
            )
            == expected
        )

    def test_services_dns_backend(self):
        settings.PROXIES_CONFIG.auth_enabled = False
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location ~ /services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver kube-dns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_dns_config() == "kube-dns.kube-system.svc.cluster.local"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth="", rewrite=False
            )
            == expected
        )

        expected = r"""
location ~ /services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    proxy_pass http://plx-operation-$4.$1.svc.new-dns:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.kube-system.svc.new-dns"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth=get_auth_config(), rewrite=False
            )
            == expected
        )

    def test_services_dns_prefix(self):
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location ~ /services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
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
            get_services_location_config(
                resolver=resolver, cors="", auth=get_auth_config(), rewrite=False
            )
            == expected
        )

        expected = r"""
location ~ /services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.new-system.svc.new-dns valid=5s;
    proxy_pass http://plx-operation-$4.$1.svc.new-dns:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.new-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.new-system.svc.new-dns"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth=get_auth_config(), rewrite=False
            )
            == expected
        )


@pytest.mark.proxies_mark
class TestRewriteExternalSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_external_dns_resolver(self):
        settings.PROXIES_CONFIG.auth_enabled = False
        expected = r"""
location ~ /rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    rewrite_log on;
    rewrite ^/rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_use_resolver = False
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth="", rewrite=True, external=True
            )
            == expected
        )

        expected = r"""
location ~ /rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4-ext.$1.svc.new-dns:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.kube-system"
        settings.PROXIES_CONFIG.dns_use_resolver = True
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver,
                cors="",
                auth=get_auth_config(),
                rewrite=True,
                external=True,
            )
            == expected
        )

    def test_external_dns_backend(self):
        settings.PROXIES_CONFIG.auth_enabled = False
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location ~ /rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver kube-dns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_dns_config() == "kube-dns.kube-system.svc.cluster.local"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth="", rewrite=True, external=True
            )
            == expected
        )

        expected = r"""
location ~ /rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4-ext.$1.svc.new-dns:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.kube-system.svc.new-dns"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver,
                cors="",
                auth=get_auth_config(),
                rewrite=True,
                external=True,
            )
            == expected
        )

    def test_external_dns_prefix(self):
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location ~ /rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver coredns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
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
            get_services_location_config(
                resolver=resolver,
                cors="",
                auth=get_auth_config(),
                rewrite=True,
                external=True,
            )
            == expected
        )

        expected = r"""
location ~ /rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver kube-dns.new-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4-ext.$1.svc.new-dns:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.new-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.new-system.svc.new-dns"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver,
                cors="",
                auth=get_auth_config(),
                rewrite=True,
                external=True,
            )
            == expected
        )


@pytest.mark.proxies_mark
class TestExternalSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_external_dns_resolver(self):
        settings.PROXIES_CONFIG.auth_enabled = False
        expected = r"""
location ~ /external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_use_resolver = False
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth="", rewrite=False, external=True
            )
            == expected
        )

        expected = r"""
location ~ /external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    proxy_pass http://plx-operation-$4-ext.$1.svc.new-dns:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.kube-system"
        settings.PROXIES_CONFIG.dns_use_resolver = True
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver,
                cors="",
                auth=get_auth_config(),
                rewrite=False,
                external=True,
            )
            == expected
        )

    def test_external_dns_backend(self):
        settings.PROXIES_CONFIG.auth_enabled = False
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location ~ /external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver kube-dns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_dns_config() == "kube-dns.kube-system.svc.cluster.local"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver, cors="", auth="", rewrite=False, external=True
            )
            == expected
        )

        expected = r"""
location ~ /external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    proxy_pass http://plx-operation-$4-ext.$1.svc.new-dns:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.kube-system.svc.new-dns"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver,
                cors="",
                auth=get_auth_config(),
                rewrite=False,
                external=True,
            )
            == expected
        )

    def test_external_dns_prefix(self):
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location ~ /external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
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
            get_services_location_config(
                resolver=resolver,
                cors="",
                auth=get_auth_config(),
                rewrite=False,
                external=True,
            )
            == expected
        )

        expected = r"""
location ~ /external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver kube-dns.new-system.svc.new-dns valid=5s;
    proxy_pass http://plx-operation-$4-ext.$1.svc.new-dns:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.new-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.new-system.svc.new-dns"
        resolver = get_resolver()
        assert (
            get_services_location_config(
                resolver=resolver,
                cors="",
                auth=get_auth_config(),
                rewrite=False,
                external=True,
            )
            == expected
        )


@pytest.mark.proxies_mark
class TestPluginsSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_no_plugins(self):
        assert get_plugins_location_config(resolver="", cors="", auth="") == []

    def test_plugins(self):
        proxy_services = {"tensorboard": {"port": 6006}, "notebook": {"port": 8888}}
        assert (
            len(
                get_plugins_location_config(
                    resolver="", cors="", auth="", proxy_services=proxy_services
                )
            )
            == 2
        )

    def test_plugins_dns_resolver(self):
        settings.PROXIES_CONFIG.auth_enabled = False
        proxy_services = {"tensorboard": {"port": 6006}, "notebook": {"port": 8888}}
        expected = r"""
location ~ /tensorboard/proxy/([-_.:\w]+)/(.*) {
    rewrite_log on;
    rewrite ^/tensorboard/proxy/([-_.:\w]+)/(.*) /tensorboard/proxy/$1/$2 break;
    proxy_pass http://$1:6006;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}


location ~ /notebook/proxy/([-_.:\w]+)/(.*) {
    rewrite_log on;
    rewrite ^/notebook/proxy/([-_.:\w]+)/(.*) /notebook/proxy/$1/$2 break;
    proxy_pass http://$1:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_use_resolver = False
        resolver = get_resolver()
        assert (
            "\n".join(
                get_plugins_location_config(
                    resolver=resolver, cors="", auth="", proxy_services=proxy_services
                )
            )
            == expected
        )

        expected = r"""
location ~ /tensorboard/proxy/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/tensorboard/proxy/([-_.:\w]+)/(.*) /tensorboard/proxy/$1/$2 break;
    proxy_pass http://$1:6006;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}


location ~ /notebook/proxy/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/notebook/proxy/([-_.:\w]+)/(.*) /notebook/proxy/$1/$2 break;
    proxy_pass http://$1:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.kube-system"
        settings.PROXIES_CONFIG.dns_use_resolver = True
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        resolver = get_resolver()
        assert (
            "\n".join(
                get_plugins_location_config(
                    resolver=resolver,
                    cors="",
                    auth=get_auth_config(),
                    proxy_services=proxy_services,
                )
            )
            == expected
        )

    def test_plugins_dns_backend(self):
        proxy_services = {"tensorboard": {"port": 6006}, "notebook": {"port": 8888}}
        settings.PROXIES_CONFIG.auth_enabled = False
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location ~ /tensorboard/proxy/([-_.:\w]+)/(.*) {
    resolver kube-dns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/tensorboard/proxy/([-_.:\w]+)/(.*) /tensorboard/proxy/$1/$2 break;
    proxy_pass http://$1:6006;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}


location ~ /notebook/proxy/([-_.:\w]+)/(.*) {
    resolver kube-dns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/notebook/proxy/([-_.:\w]+)/(.*) /notebook/proxy/$1/$2 break;
    proxy_pass http://$1:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_dns_config() == "kube-dns.kube-system.svc.cluster.local"
        resolver = get_resolver()
        assert (
            "\n".join(
                get_plugins_location_config(
                    resolver=resolver, cors="", auth="", proxy_services=proxy_services
                )
            )
            == expected
        )

        expected = r"""
location ~ /tensorboard/proxy/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/tensorboard/proxy/([-_.:\w]+)/(.*) /tensorboard/proxy/$1/$2 break;
    proxy_pass http://$1:6006;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}


location ~ /notebook/proxy/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.kube-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/notebook/proxy/([-_.:\w]+)/(.*) /notebook/proxy/$1/$2 break;
    proxy_pass http://$1:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.kube-system.svc.new-dns"
        resolver = get_resolver()
        assert (
            "\n".join(
                get_plugins_location_config(
                    resolver=resolver,
                    cors="",
                    auth=get_auth_config(),
                    proxy_services=proxy_services,
                )
            )
            == expected
        )

    def test_plugins_dns_prefix(self):
        proxy_services = {"tensorboard": {"port": 6006}, "notebook": {"port": 8888}}
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.dns_use_resolver = True
        expected = r"""
location ~ /tensorboard/proxy/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/tensorboard/proxy/([-_.:\w]+)/(.*) /tensorboard/proxy/$1/$2 break;
    proxy_pass http://$1:6006;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}


location ~ /notebook/proxy/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/notebook/proxy/([-_.:\w]+)/(.*) /notebook/proxy/$1/$2 break;
    proxy_pass http://$1:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_prefix = "coredns.kube-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_dns_config() == "coredns.kube-system.svc.cluster.local"
        resolver = get_resolver()
        assert (
            "\n".join(
                get_plugins_location_config(
                    resolver=resolver,
                    cors="",
                    auth=get_auth_config(),
                    proxy_services=proxy_services,
                )
            )
            == expected
        )

        expected = r"""
location ~ /tensorboard/proxy/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.new-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/tensorboard/proxy/([-_.:\w]+)/(.*) /tensorboard/proxy/$1/$2 break;
    proxy_pass http://$1:6006;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}


location ~ /notebook/proxy/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver kube-dns.new-system.svc.new-dns valid=5s;
    rewrite_log on;
    rewrite ^/notebook/proxy/([-_.:\w]+)/(.*) /notebook/proxy/$1/$2 break;
    proxy_pass http://$1:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.dns_prefix = "kube-dns.new-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "new-dns"
        assert get_dns_config() == "kube-dns.new-system.svc.new-dns"
        resolver = get_resolver()
        assert (
            "\n".join(
                get_plugins_location_config(
                    resolver=resolver,
                    cors="",
                    auth=get_auth_config(),
                    proxy_services=proxy_services,
                )
            )
            == expected
        )
