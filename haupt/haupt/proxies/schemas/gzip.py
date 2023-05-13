from haupt.proxies.schemas.base import get_config

OPTIONS = """
gzip                        on;
gzip_disable                "msie6";
gzip_types                  *;
gzip_proxied                any;
"""


def get_gzip_config():
    return get_config(options=OPTIONS, indent=0)
