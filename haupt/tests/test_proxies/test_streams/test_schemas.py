#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import pytest

from haupt.proxies.schemas.locations import get_streams_locations_config
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestStreamsLocationSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_locations(self):
        expected = """
location /tmp/ {
    alias                     /tmp/;
    expires                   0;
    add_header                Cache-Control private;
    internal;
}


location /tmp/plx/archives/ {
    alias                     /tmp/plx/archives/;
    expires                   0;
    add_header                Cache-Control private;
    set                       $x_content_length $upstream_http_x_content_length;
    add_header                X-Content-Length $x_content_length;
    internal;
}
"""  # noqa
        assert get_streams_locations_config() == expected
