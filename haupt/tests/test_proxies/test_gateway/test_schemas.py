#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import pytest

from haupt import settings
from haupt.proxies.schemas.gateway.api import get_api_location_config
from haupt.proxies.schemas.gateway.redirect import get_redirect_config
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestGatewaySchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_redirect_config(self):
        expected = r"""
server {
    listen 80;
    return 301 https://$host$request_uri;
}
"""  # noqa
        settings.PROXIES_CONFIG.ssl_enabled = False
        assert get_redirect_config() == ""
        settings.PROXIES_CONFIG.ssl_enabled = True
        assert get_redirect_config() == expected


@pytest.mark.proxies_mark
class TestGatewayApiSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_api_location_config(self):
        expected = r"""
location = / {
    proxy_pass http://polyaxon-polyaxon-api;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}


location /api/v1/ {
    proxy_pass http://polyaxon-polyaxon-api;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}


location /auth/v1/ {
    proxy_pass http://polyaxon-polyaxon-api;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}


location /ui/ {
    proxy_pass http://polyaxon-polyaxon-api;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}


location /sso/ {
    proxy_pass http://polyaxon-polyaxon-api;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}


location /static/ {
    proxy_pass http://polyaxon-polyaxon-api;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}
"""  # noqa
        assert get_api_location_config(resolver="") == expected

        settings.PROXIES_CONFIG.api_port = 8888
        settings.PROXIES_CONFIG.api_host = "foo"
        expected = r"""
location = / {
    proxy_pass http://foo:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}


location /api/v1/ {
    proxy_pass http://foo:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}


location /auth/v1/ {
    proxy_pass http://foo:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}


location /ui/ {
    proxy_pass http://foo:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}


location /sso/ {
    proxy_pass http://foo:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}


location /static/ {
    proxy_pass http://foo:8888;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}
"""  # noqa
        assert get_api_location_config(resolver="") == expected

        settings.PROXIES_CONFIG.api_port = 443
        settings.PROXIES_CONFIG.api_host = "polyaxon.foo.com"
        expected = r"""
location = / {
    proxy_ssl_server_name on;
    proxy_pass https://polyaxon.foo.com;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host polyaxon.foo.com;
    proxy_buffering off;
}


location /api/v1/ {
    proxy_ssl_server_name on;
    proxy_pass https://polyaxon.foo.com;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host polyaxon.foo.com;
    proxy_buffering off;
}


location /auth/v1/ {
    proxy_ssl_server_name on;
    proxy_pass https://polyaxon.foo.com;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host polyaxon.foo.com;
    proxy_buffering off;
}


location /ui/ {
    proxy_ssl_server_name on;
    proxy_pass https://polyaxon.foo.com;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host polyaxon.foo.com;
    proxy_buffering off;
}


location /sso/ {
    proxy_ssl_server_name on;
    proxy_pass https://polyaxon.foo.com;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host polyaxon.foo.com;
    proxy_buffering off;
}


location /static/ {
    proxy_ssl_server_name on;
    proxy_pass https://polyaxon.foo.com;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host polyaxon.foo.com;
    proxy_buffering off;
}
"""  # noqa
        assert get_api_location_config(resolver="") == expected

        # Add proxy
        settings.PROXIES_CONFIG.has_forward_proxy = True
        settings.PROXIES_CONFIG.forward_proxy_port = 443
        settings.PROXIES_CONFIG.forward_proxy_host = "moo.foo.com"
        expected = r"""
location = / {
    proxy_ssl_server_name on;
    proxy_pass https://127.0.0.1:8443;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host polyaxon.foo.com;
    proxy_buffering off;
}


location /api/v1/ {
    proxy_ssl_server_name on;
    proxy_pass https://127.0.0.1:8443;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host polyaxon.foo.com;
    proxy_buffering off;
}


location /auth/v1/ {
    proxy_ssl_server_name on;
    proxy_pass https://127.0.0.1:8443;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host polyaxon.foo.com;
    proxy_buffering off;
}


location /ui/ {
    proxy_ssl_server_name on;
    proxy_pass https://127.0.0.1:8443;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host polyaxon.foo.com;
    proxy_buffering off;
}


location /sso/ {
    proxy_ssl_server_name on;
    proxy_pass https://127.0.0.1:8443;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host polyaxon.foo.com;
    proxy_buffering off;
}


location /static/ {
    proxy_ssl_server_name on;
    proxy_pass https://127.0.0.1:8443;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host polyaxon.foo.com;
    proxy_buffering off;
}
"""  # noqa
        assert get_api_location_config(resolver="") == expected
