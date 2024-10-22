import pytest

from haupt import settings
from haupt.proxies.schemas.api.base import get_base_config
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestApiBase(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_api_base_config(self):
        expected = """
listen 8000;


error_log /tmp/logs/error.log warn;


gzip                        on;
gzip_disable                "msie6";
gzip_types                  *;
gzip_proxied                any;


charset utf-8;


client_max_body_size        0;
client_body_buffer_size     50m;
client_body_in_file_only clean;
large_client_header_buffers 8 1m;
client_header_buffer_size 1m;
uwsgi_buffer_size 1m;
uwsgi_buffers 8 1m;
uwsgi_busy_buffers_size 2m;
sendfile on;


send_timeout 650;
keepalive_timeout 650;
uwsgi_read_timeout 650;
uwsgi_send_timeout 650;
client_header_timeout 650;
proxy_read_timeout 650;
keepalive_requests 10000;


location = / {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors on;
}


location = /healthz/ {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors off;
}


location /api/v1/ {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors off;
}


location /auth/v1/ {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors off;
}


location /sso/ {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors off;
}


location /ui/ {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors on;
}


error_page 500 502 503 504 /static/errors/50x.html;
error_page 401 403 /static/errors/permission.html;
error_page 404 /static/errors/404.html;


location = /robots.txt {
    rewrite ^ /static/robots.txt;
}


location = /favicon.ico {
    rewrite ^ /static/images/favicon.ico;
}


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
        assert get_base_config() == expected

    def test_api_base_config_with_cdn_and_admin(self):
        expected = """
listen 8000;


error_log /tmp/logs/error.log warn;


gzip                        on;
gzip_disable                "msie6";
gzip_types                  *;
gzip_proxied                any;


charset utf-8;


client_max_body_size        0;
client_body_buffer_size     50m;
client_body_in_file_only clean;
large_client_header_buffers 8 1m;
client_header_buffer_size 1m;
uwsgi_buffer_size 1m;
uwsgi_buffers 8 1m;
uwsgi_busy_buffers_size 2m;
sendfile on;


send_timeout 650;
keepalive_timeout 650;
uwsgi_read_timeout 650;
uwsgi_send_timeout 650;
client_header_timeout 650;
proxy_read_timeout 650;
keepalive_requests 10000;


location = / {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors on;
}


location = /healthz/ {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors off;
}


location /api/v1/ {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors off;
}


location /auth/v1/ {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors off;
}


location /sso/ {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors off;
}


location /ui/ {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors on;
}


location /_admin/ {
    include     /etc/nginx/uwsgi_params;
    uwsgi_pass  polyaxon;
    uwsgi_param Host				$host;
    uwsgi_param X-Real-IP			$remote_addr;
    uwsgi_param X-Forwarded-For		$proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto	$http_x_forwarded_proto;
    uwsgi_intercept_errors on;
}


error_page 500 502 503 504 /static/errors/50x.html;
error_page 401 403 /static/errors/permission.html;
error_page 404 /static/errors/404.html;


location = /robots.txt {
    rewrite ^ /static/robots.txt;
}


location = /favicon.ico {
    rewrite ^ /static/images/favicon.ico;
}


location /static/ {
    proxy_ssl_server_name on;
    proxy_pass https://cdn.foo.bar/;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
}


location /tmp/ {
    alias                     /tmp/;
    expires                   0;
    add_header                Cache-Control private;
    internal;
}
"""  # noqa
        settings.PROXIES_CONFIG.ui_admin_enabled = True
        settings.PROXIES_CONFIG.static_url = "https://cdn.foo.bar"
        assert get_base_config() == expected
