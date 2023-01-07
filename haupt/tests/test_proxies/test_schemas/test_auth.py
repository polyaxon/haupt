#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import pytest

from haupt import settings
from haupt.proxies.schemas.auth import get_auth_config, get_auth_location_config
from haupt.proxies.schemas.dns import get_dns_config, get_resolver
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestAuthSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_auth_config(self):
        settings.PROXIES_CONFIG.auth_enabled = True
        expected = r"""
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;
"""  # noqa
        assert get_auth_config() == expected

        settings.PROXIES_CONFIG.auth_enabled = False
        assert get_auth_config() == ""

    def test_auth_config_with_external_service(self):
        settings.PROXIES_CONFIG.auth_enabled = True
        expected = r"""
    auth_request     /auth/v1/;
    auth_request_set $auth_status $upstream_status;
"""  # noqa
        assert get_auth_config(auth_api="/auth/v1/") == expected

        settings.PROXIES_CONFIG.auth_enabled = False
        assert get_auth_config() == ""

    def test_auth_location_config(self):
        settings.PROXIES_CONFIG.auth_use_resolver = False
        settings.PROXIES_CONFIG.dns_use_resolver = False
        settings.PROXIES_CONFIG.auth_enabled = True
        expected = r"""
location = /auth/v1/ {
    proxy_pass http://polyaxon-polyaxon-api;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
    proxy_set_header Host $http_host;
    internal;
}
"""  # noqa
        assert get_auth_location_config(resolver="") == expected

        # Use resolver but do not enable it for auth
        settings.PROXIES_CONFIG.dns_use_resolver = True
        settings.PROXIES_CONFIG.dns_prefix = "coredns.kube-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_dns_config() == "coredns.kube-system.svc.cluster.local"
        resolver = get_resolver()

        expected = r"""
location = /auth/v1/ {
    proxy_pass http://polyaxon-polyaxon-api;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
    proxy_set_header Host $http_host;
    internal;
}
"""  # noqa
        assert get_auth_location_config(resolver=resolver) == expected

        # Enable resolver for auth
        settings.PROXIES_CONFIG.auth_use_resolver = True
        expected = r"""
location = /auth/v1/ {
    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://polyaxon-polyaxon-api;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
    proxy_set_header Host $http_host;
    internal;
}
"""  # noqa
        assert get_auth_location_config(resolver=resolver) == expected

    def test_external_auth_location_config(self):
        settings.PROXIES_CONFIG.auth_use_resolver = False
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.auth_external = "https://cloud.polyaxon.com"
        expected = r"""
location = /auth/v1/ {
    proxy_ssl_server_name on;
    proxy_pass https://cloud.polyaxon.com;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
    proxy_set_header Host cloud.polyaxon.com;
    internal;
}
"""  # noqa
        assert get_auth_location_config(resolver="") == expected

        # Add proxy
        settings.PROXIES_CONFIG.has_forward_proxy = True
        settings.PROXIES_CONFIG.forward_proxy_port = 443
        settings.PROXIES_CONFIG.forward_proxy_host = "123.123.123.123"

        expected = r"""
location = /auth/v1/ {
    proxy_ssl_server_name on;
    proxy_pass https://127.0.0.1:8443;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
    proxy_set_header Host cloud.polyaxon.com;
    internal;
}
"""  # noqa
        assert get_auth_location_config(resolver="") == expected

        # Use resolver but do not enable it for auth
        settings.PROXIES_CONFIG.has_forward_proxy = False
        settings.PROXIES_CONFIG.dns_use_resolver = True
        settings.PROXIES_CONFIG.dns_prefix = "coredns.kube-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_dns_config() == "coredns.kube-system.svc.cluster.local"
        resolver = get_resolver()

        expected = r"""
location = /auth/v1/ {
    proxy_ssl_server_name on;
    proxy_pass https://cloud.polyaxon.com;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
    proxy_set_header Host cloud.polyaxon.com;
    internal;
}
"""  # noqa
        assert get_auth_location_config(resolver=resolver) == expected

        # Add proxy
        settings.PROXIES_CONFIG.has_forward_proxy = True

        expected = r"""
location = /auth/v1/ {
    proxy_ssl_server_name on;
    proxy_pass https://127.0.0.1:8443;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
    proxy_set_header Host cloud.polyaxon.com;
    internal;
}
"""  # noqa
        assert get_auth_location_config(resolver="") == expected
