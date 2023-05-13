import pytest

from haupt.proxies.schemas.locations import get_api_locations_config
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestApiSchemas(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_api_locations(self):
        expected = """
location /static/ {
    alias /static/v1/;
    autoindex on;
    expires                   30d;
    add_header                Cache-Control private;
    gzip_static on;
}


location /tmp/ {
    alias                     /tmp/;
    expires                   0;
    add_header                Cache-Control private;
    internal;
}
"""  # noqa
        assert get_api_locations_config() == expected
