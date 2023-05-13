from haupt import settings
from haupt.proxies.schemas.base import get_config

SSL_OPTIONS = r"""
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

ssl_certificate      {ssl_path}/polyaxon.com.crt;
ssl_certificate_key  {ssl_path}/polyaxon.com.key;
"""  # noqa


def get_ssl_config():
    return get_config(
        options=SSL_OPTIONS, indent=0, ssl_path=settings.PROXIES_CONFIG.ssl_path
    )
