#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import pytest

from haupt import settings
from haupt.proxies.schemas.listen import get_listen_config
from haupt.proxies.schemas.logging import get_logging_config
from haupt.proxies.schemas.ssl import get_ssl_config
from haupt.proxies.schemas.timeout import get_timeout_config
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestBaseSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_ssl(self):
        expected = r"""
# SSL
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_session_tickets off;

# intermediate configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers on;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 1.1.1.1 1.0.0.1 [2606:4700:4700::1111] [2606:4700:4700::1001] 8.8.8.8 8.8.4.4 [2001:4860:4860::8888] [2001:4860:4860::8844] 208.67.222.222 208.67.220.220 [2620:119:35::35] [2620:119:53::53] valid=60s;
resolver_timeout 2s;

ssl_certificate      /etc/ssl/polyaxon/polyaxon.com.crt;
ssl_certificate_key  /etc/ssl/polyaxon/polyaxon.com.key;
"""  # noqa
        assert get_ssl_config() == expected

        expected = r"""
# SSL
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_session_tickets off;

# intermediate configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers on;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 1.1.1.1 1.0.0.1 [2606:4700:4700::1111] [2606:4700:4700::1001] 8.8.8.8 8.8.4.4 [2001:4860:4860::8888] [2001:4860:4860::8844] 208.67.222.222 208.67.220.220 [2620:119:35::35] [2620:119:53::53] valid=60s;
resolver_timeout 2s;

ssl_certificate      /foo/polyaxon.com.crt;
ssl_certificate_key  /foo/polyaxon.com.key;
"""  # noqa
        settings.PROXIES_CONFIG.ssl_path = "/foo"
        assert get_ssl_config() == expected

    def test_timeout(self):
        expected = """
send_timeout 200;
keepalive_timeout 200;
uwsgi_read_timeout 200;
uwsgi_send_timeout 200;
client_header_timeout 200;
proxy_read_timeout 200;
keepalive_requests 10000;
"""  # noqa
        settings.PROXIES_CONFIG.nginx_timeout = 200
        assert get_timeout_config() == expected

    def test_listen(self):
        expected = """
listen 8000;
"""  # noqa
        settings.PROXIES_CONFIG.ssl_enabled = False
        assert get_listen_config(is_proxy=False) == expected

        settings.PROXIES_CONFIG.ssl_enabled = True
        assert get_listen_config(is_proxy=False) == expected

    def test_proxy_listen(self):
        expected = """
listen 8000;
"""  # noqa
        settings.PROXIES_CONFIG.ssl_enabled = False
        assert get_listen_config(is_proxy=True) == expected

        expected = """
listen 443 ssl;
ssl on;
"""  # noqa
        settings.PROXIES_CONFIG.ssl_enabled = True
        assert get_listen_config(is_proxy=True) == expected

    def test_logging(self):
        expected = """
error_log /tmp/logs/error.log warn;
"""  # noqa
        settings.PROXIES_CONFIG.log_level = "warn"
        assert get_logging_config() == expected
