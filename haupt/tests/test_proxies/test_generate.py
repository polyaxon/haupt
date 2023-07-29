import os
import pytest
import tempfile

from clipped.compact.pydantic import ValidationError

from haupt import settings
from haupt.proxies.generators import (
    generate_api_conf,
    generate_forward_proxy_cmd,
    generate_gateway_conf,
    generate_streams_conf,
)
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestGenerate(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_generate_api_conf(self):
        tmp_dir = tempfile.mkdtemp()
        assert os.listdir(tmp_dir) == []
        generate_api_conf(path=tmp_dir)
        assert set(os.listdir(tmp_dir)) == {"polyaxon.main.conf", "polyaxon.base.conf"}

    def test_generate_gateway_conf(self):
        tmp_dir = tempfile.mkdtemp()
        assert os.listdir(tmp_dir) == []
        generate_gateway_conf(path=tmp_dir)
        assert set(os.listdir(tmp_dir)) == {
            "polyaxon.main.conf",
            "polyaxon.base.conf",
            "polyaxon.redirect.conf",
        }

    def test_generate_forward_proxy_conf(self):
        tmp_dir = tempfile.mkdtemp()
        assert os.listdir(tmp_dir) == []
        generate_forward_proxy_cmd(path=tmp_dir)
        assert os.listdir(tmp_dir) == []

        settings.PROXIES_CONFIG.has_forward_proxy = True
        settings.PROXIES_CONFIG.forward_proxy_port = 443
        settings.PROXIES_CONFIG.forward_proxy_host = "123.123.123.123"
        generate_forward_proxy_cmd(path=tmp_dir)
        assert os.listdir(tmp_dir) == ["forward_proxy.sh"]

    def test_generate_forward_proxy_conf_valid_kind(self):
        tmp_dir = tempfile.mkdtemp()
        assert os.listdir(tmp_dir) == []
        settings.PROXIES_CONFIG.forward_proxy_kind = "connect"
        generate_forward_proxy_cmd(path=tmp_dir)
        assert os.listdir(tmp_dir) == []

        settings.PROXIES_CONFIG.has_forward_proxy = True
        settings.PROXIES_CONFIG.forward_proxy_port = 443
        settings.PROXIES_CONFIG.forward_proxy_host = "123.123.123.123"
        generate_forward_proxy_cmd(path=tmp_dir)
        assert os.listdir(tmp_dir) == ["forward_proxy.sh"]

    def test_generate_forward_proxy_conf_wrong_kind(self):
        tmp_dir = tempfile.mkdtemp()
        assert os.listdir(tmp_dir) == []

        assert settings.PROXIES_CONFIG.forward_proxy_kind is None
        with self.assertRaises(ValidationError):
            settings.PROXIES_CONFIG.forward_proxy_kind = "foo"

        assert settings.PROXIES_CONFIG.forward_proxy_kind is None
        generate_forward_proxy_cmd(path=tmp_dir)
        assert os.listdir(tmp_dir) == []

        # Will use default value
        settings.PROXIES_CONFIG.has_forward_proxy = True
        settings.PROXIES_CONFIG.forward_proxy_port = 443
        settings.PROXIES_CONFIG.forward_proxy_host = "123.123.123.123"
        generate_forward_proxy_cmd(path=tmp_dir)
        assert os.listdir(tmp_dir) == ["forward_proxy.sh"]

    def test_generate_streams_conf(self):
        tmp_dir = tempfile.mkdtemp()
        assert os.listdir(tmp_dir) == []
        generate_streams_conf(path=tmp_dir)
        assert set(os.listdir(tmp_dir)) == {"polyaxon.main.conf", "polyaxon.base.conf"}
