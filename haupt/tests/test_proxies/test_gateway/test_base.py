import pytest

from haupt import settings
from haupt.proxies.schemas.gateway import get_base_config
from tests.test_proxies.base import BaseProxiesTestCase


@pytest.mark.proxies_mark
class TestGatewayBase(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_gateway_base_config(self):
        expected = r"""
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


error_page 500 502 503 504 /static/errors/50x.html;
error_page 401 403 /static/errors/permission.html;
error_page 404 /static/errors/404.html;


location = /robots.txt {
    rewrite ^ /static/robots.txt;
}


location = /favicon.ico {
    rewrite ^ /static/images/favicon.ico;
}


location /internal/ {
    proxy_pass http://polyaxon-polyaxon-streams;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location /streams/ {
    proxy_pass http://polyaxon-polyaxon-streams;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location /k8s/ {
    proxy_pass http://polyaxon-polyaxon-streams;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    rewrite_log on;
    rewrite ^/rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    rewrite_log on;
    rewrite ^/rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /monitors/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    proxy_pass http://$5.$1.svc.cluster.local:$6;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /rewrite-monitors/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    rewrite_log on;
    rewrite ^/rewrite-monitors/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) /$7 break;
    proxy_pass http://$5.$1.svc.cluster.local:$6;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


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


location /healthz/ {
    access_log off;
    return 200 "healthy";
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = False
        settings.PROXIES_CONFIG.dns_use_resolver = False
        assert get_base_config(is_platform=False) == expected

    def test_gateway_base_config_with_auth_and_dns(self):
        expected = r"""
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


error_page 500 502 503 504 /static/errors/50x.html;
error_page 401 403 /static/errors/permission.html;
error_page 404 /static/errors/404.html;


location = /robots.txt {
    rewrite ^ /static/robots.txt;
}


location = /favicon.ico {
    rewrite ^ /static/images/favicon.ico;
}


location /internal/ {
    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://polyaxon-polyaxon-streams;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location /streams/ {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://polyaxon-polyaxon-streams;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location /k8s/ {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://polyaxon-polyaxon-streams;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver coredns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /monitors/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://$5.$1.svc.cluster.local:$6;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /rewrite-monitors/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-monitors/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) /$7 break;
    proxy_pass http://$5.$1.svc.cluster.local:$6;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location = / {
    resolver coredns.kube-system.svc.cluster.local valid=5s;
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
    resolver coredns.kube-system.svc.cluster.local valid=5s;
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
    resolver coredns.kube-system.svc.cluster.local valid=5s;
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
    resolver coredns.kube-system.svc.cluster.local valid=5s;
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
    resolver coredns.kube-system.svc.cluster.local valid=5s;
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
    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://polyaxon-polyaxon-api;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}


location /_admin/ {
    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://polyaxon-polyaxon-api;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $http_host;
    proxy_buffering off;
}


location /healthz/ {
    access_log off;
    return 200 "healthy";
}
"""  # noqa
        settings.PROXIES_CONFIG.ui_admin_enabled = True
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.auth_use_resolver = True
        settings.PROXIES_CONFIG.api_use_resolver = True
        settings.PROXIES_CONFIG.dns_use_resolver = True
        settings.PROXIES_CONFIG.dns_prefix = "coredns.kube-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_base_config(is_platform=False) == expected


@pytest.mark.proxies_mark
class TestPlatformBase(BaseProxiesTestCase):
    SET_PROXIES_SETTINGS = True

    def test_platform_base_config(self):
        expected = r"""
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
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors on;
}


location = /healthz/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors off;
}


location /api/v1/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors off;
}


location /auth/v1/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors off;
}


location /sso/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors off;
}


location /ui/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors on;
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


location = /auth-request/v1/ {
    proxy_pass http://polyaxon;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
    proxy_set_header Host $http_host;
    proxy_intercept_errors off;
    internal;
}


location /internal/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location /streams/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location /k8s/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    rewrite_log on;
    rewrite ^/rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    rewrite_log on;
    rewrite ^/rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /monitors/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    proxy_pass http://$5.$1.svc.cluster.local:$6;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /rewrite-monitors/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    rewrite_log on;
    rewrite ^/rewrite-monitors/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) /$7 break;
    proxy_pass http://$5.$1.svc.cluster.local:$6;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
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


location /tmp/plx/archives/ {
    alias                     /tmp/plx/archives/;
    expires                   0;
    add_header                Cache-Control private;
    set                       $x_content_length $upstream_http_x_content_length;
    add_header                X-Content-Length $x_content_length;
    internal;
}


location /k8s/v1/ {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;
    auth_request_set $k8s_token $upstream_http_k8s_token;
    auth_request_set $k8s_uri $upstream_http_k8s_uri;
    proxy_pass $k8s_uri;
    proxy_http_version 1.1;
    proxy_redirect     off;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Authorization "bearer $k8s_token";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.auth_enabled = False
        settings.PROXIES_CONFIG.dns_use_resolver = False
        assert get_base_config(is_platform=True) == expected

    def test_platform_base_config_with_auth_and_dns(self):
        expected = r"""
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
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors on;
}


location = /healthz/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors off;
}


location /api/v1/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors off;
}


location /auth/v1/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors off;
}


location /sso/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors off;
}


location /ui/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors on;
}


location /_admin/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors on;
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


location = /auth-request/v1/ {
    proxy_pass http://polyaxon;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_set_header X-Origin-Method $request_method;
    proxy_set_header Host $http_host;
    proxy_intercept_errors off;
    internal;
}


location /internal/ {
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location /streams/ {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location /k8s/ {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-services/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    resolver coredns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-external/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/(.*) /$6 break;
    proxy_pass http://plx-operation-$4-ext.$1.svc.cluster.local:$5;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /monitors/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    proxy_pass http://$5.$1.svc.cluster.local:$6;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}


location ~ /rewrite-monitors/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;

    resolver coredns.kube-system.svc.cluster.local valid=5s;
    rewrite_log on;
    rewrite ^/rewrite-monitors/v1/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/runs/([-_.:\w]+)/([-_.:\w]+)/([-_.:\w]+)/(.*) /$7 break;
    proxy_pass http://$5.$1.svc.cluster.local:$6;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
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


location /tmp/plx/archives/ {
    alias                     /tmp/plx/archives/;
    expires                   0;
    add_header                Cache-Control private;
    set                       $x_content_length $upstream_http_x_content_length;
    add_header                X-Content-Length $x_content_length;
    internal;
}


location /k8s/v1/ {
    auth_request     /auth-request/v1/;
    auth_request_set $auth_status $upstream_status;
    auth_request_set $k8s_token $upstream_http_k8s_token;
    auth_request_set $k8s_uri $upstream_http_k8s_uri;
    proxy_pass $k8s_uri;
    proxy_http_version 1.1;
    proxy_redirect     off;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_hide_header X-Frame-Options;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Authorization "bearer $k8s_token";
    proxy_buffering off;
}
"""  # noqa
        settings.PROXIES_CONFIG.ui_admin_enabled = True
        settings.PROXIES_CONFIG.auth_enabled = True
        settings.PROXIES_CONFIG.auth_use_resolver = True
        settings.PROXIES_CONFIG.api_use_resolver = True
        settings.PROXIES_CONFIG.dns_use_resolver = True
        settings.PROXIES_CONFIG.dns_prefix = "coredns.kube-system"
        settings.PROXIES_CONFIG.dns_custom_cluster = "cluster.local"
        assert get_base_config(is_platform=True) == expected
