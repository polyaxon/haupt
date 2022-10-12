#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import pytest

from haupt.proxies.schemas.gateway.main import get_main_config
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestGatewayMain(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_base_config(self):
        expected = """
server {
    include polyaxon/polyaxon.base.conf;
}

include polyaxon/polyaxon.redirect.conf;
"""  # noqa
        assert get_main_config() == expected
