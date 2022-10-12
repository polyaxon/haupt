#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import pytest

from haupt import settings
from haupt.proxies.schemas.listen import get_listen_config
from haupt.proxies.schemas.logging import get_logging_config
from haupt.proxies.schemas.timeout import get_timeout_config
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestBaseSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

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
error_log /polyaxon/logs/error.log warn;
"""  # noqa
        settings.PROXIES_CONFIG.log_level = "warn"
        assert get_logging_config() == expected
