#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import pytest

from haupt.proxies.schemas.api.main import get_main_config
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestApiMain(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_base_config(self):
        expected = """
upstream polyaxon {
  server unix:/polyaxon/web/polyaxon.sock;
}

server {
    include polyaxon/polyaxon.base.conf;
}
"""  # noqa
        assert get_main_config() == expected
